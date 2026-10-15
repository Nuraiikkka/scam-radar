"""Exploratory binary transcript+OCR baseline. Does not modify the live API."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score,
                             classification_report, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.services.text_classifier import classify


def input_text(row):
    # Deliberately exclude category, directory, verdict, rationale and metadata.
    return re.sub(r'\s+', ' ', row.get('transcript', '') + ' ' + row.get('ocr_text', '')).strip()


def duplicate_groups(rows, texts):
    """Connected components of IDs, known authors, exact/near text duplicates.

    Similarity index is used for splitting only; model vocabulary is fitted
    exclusively on training data. Missing author IDs remain a limitation.
    """
    parents = list(range(len(rows)))

    def find(a):
        while parents[a] != a:
            parents[a] = parents[parents[a]]
            a = parents[a]
        return a

    def union(a, b):
        parents[find(a)] = find(b)

    seen = {}
    for i, (row, text) in enumerate(zip(rows, texts)):
        keys = [('id', row['id']), ('text', text.lower())]
        if row.get('author_id'):
            keys.append(('author', row['author_id']))
        for key in keys:
            if key in seen:
                union(i, seen[key])
            else:
                seen[key] = i
    matrix = TfidfVectorizer(analyzer='char_wb', ngram_range=(4, 5), max_features=50000).fit_transform(texts)
    neighbors = NearestNeighbors(metric='cosine', algorithm='brute').fit(matrix)
    distances, indices = neighbors.radius_neighbors(matrix, radius=0.08)
    for i, (ds, js) in enumerate(zip(distances, indices)):
        for distance, j in zip(ds, js):
            if i != j and distance <= 0.08:
                union(i, int(j))
    return np.array([find(i) for i in range(len(rows))])


def split_indices(y, groups, inspected):
    # Split selection uses labels only to ensure both classes are represented;
    # no predictions/test metrics are used to choose a split.
    for seed in range(42, 142):
        train_val, test = next(GroupShuffleSplit(n_splits=1, test_size=.2, random_state=seed).split(y, y, groups))
        train_local, val_local = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=seed).split(train_val, y[train_val], groups[train_val]))
        train, val = train_val[train_local], train_val[val_local]
        if all(len(set(y[idx])) == 2 for idx in [train, val, test]):
            # The single sample manually inspected during source audit is for
            # development only, together with any duplicate component.
            if inspected.intersection(set(groups[val]) | set(groups[test])):
                continue
            return train, val, test, seed
    raise ValueError('Cannot create three independent groups with both classes')


def metrics(y, pred, scores=None):
    result = {
        'n': len(y), 'accuracy': accuracy_score(y, pred),
        'macro_f1': f1_score(y, pred, average='macro', zero_division=0),
        'scam_precision': precision_score(y, pred, zero_division=0),
        'scam_recall': recall_score(y, pred, zero_division=0),
        'confusion_matrix_rows_true_0legitimate_1scam': confusion_matrix(y, pred, labels=[0, 1]).tolist(),
        'classification_report': classification_report(y, pred, labels=[0, 1], target_names=['legitimate', 'scam'], zero_division=0, output_dict=True),
    }
    if scores is not None and len(set(y)) == 2:
        result['roc_auc'] = roc_auc_score(y, scores)
        result['average_precision'] = average_precision_score(y, scores)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'data/processed/optiscam.jsonl')
    args = parser.parse_args()
    raw = args.data.read_bytes()
    records = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    rows, excluded = [], []
    for row in records:
        if row['label'] not in {'scam', 'legitimate'}:
            raise ValueError('Unknown label')
        if len(input_text(row)) < 40:
            excluded.append(row['id'])
        else:
            rows.append(row)
    if len(rows) < 40:
        raise ValueError('Need at least 40 nonempty records for an exploratory split')
    texts = [input_text(row) for row in rows]
    y = np.array([int(row['label'] == 'scam') for row in rows])
    groups = duplicate_groups(rows, texts)
    inspected = {groups[i] for i, row in enumerate(rows) if row['id'] == 'youtube_958FabPvsYM'}
    train, val, test, seed = split_indices(y, groups, inspected)
    assert not (set(groups[train]) & set(groups[val]) or set(groups[train]) & set(groups[test]) or set(groups[val]) & set(groups[test]))
    candidates = []
    for c in [.5, 2.0]:
        model = Pipeline([
            ('features', FeatureUnion([
                ('word', TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=30000)),
                ('char', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=2, sublinear_tf=True, max_features=40000)),
            ])),
            ('classifier', LogisticRegression(C=c, class_weight='balanced', max_iter=1000, random_state=42)),
        ])
        model.fit([texts[i] for i in train], y[train])
        scores = model.predict_proba([texts[i] for i in val])[:, 1]
        for threshold in np.arange(.25, .76, .05):
            value = f1_score(y[val], scores >= threshold, average='macro', zero_division=0)
            candidates.append((value, -abs(threshold-.5), c, float(threshold), model))
    best = max(candidates, key=lambda result: result[:2])
    _, _, c, threshold, model = best
    # Freeze model and threshold before the single held-out test evaluation.
    test_scores = model.predict_proba([texts[i] for i in test])[:, 1]
    pred = (test_scores >= threshold).astype(int)
    rule_pred = np.array([int(classify(texts[i])[0] != 'none') for i in test])
    report = {
        'experiment': 'exploratory_binary_transcript_ocr',
        'dataset_sha256': hashlib.sha256(raw).hexdigest(), 'sklearn_version': sklearn.__version__,
        'label_source': 'OptiScam weak labels; not independently human verified',
        'license': 'CC BY-NC-SA 4.0; research/non-commercial experiment',
        'features': ['transcript', 'ocr_text'], 'excluded_short_ids': excluded,
        'rows': len(rows), 'duplicate_components': len(set(groups)), 'split_seed': seed,
        'split': {name: {'n':len(idx), 'labels':dict(Counter(rows[i]['label'] for i in idx)), 'topics':dict(Counter(rows[i]['source_topic'] for i in idx))} for name, idx in [('train',train),('validation',val),('test',test)]},
        'C': c, 'threshold_selected_on_validation': threshold,
        'validation_macro_f1': best[0], 'test': metrics(y[test], pred, test_scores),
        'rules_test_same_records': metrics(y[test], rule_pred),
        'per_topic_test': {},
        'limitations': [
            'Binary source labels do not support all five project scam categories.',
            'No independent human relabeling performed; scores measure agreement with weak source labels.',
            'Author IDs unavailable; cross-author independence cannot be established.',
            'Exact and near text duplicates grouped, but visual/reupload duplicates may remain.',
            'No fresh TikTok, Russian or Kazakh holdout evaluation.',
            'Uses supplied ASR/OCR, not end-to-end evaluation of video processing.',
            'Balanced sample does not represent real-world prevalence; probabilities are uncalibrated.',
        ],
    }
    for topic in sorted({rows[i]['source_topic'] for i in test}):
        positions = [j for j,i in enumerate(test) if rows[i]['source_topic'] == topic]
        report['per_topic_test'][topic] = metrics(y[test][positions], pred[positions], test_scores[positions])
    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)
    (reports / 'baseline_metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    with (reports / 'split_manifest.jsonl').open('w', encoding='utf-8') as handle:
        for split, indices in [('train',train),('validation',val),('test',test)]:
            for i in indices:
                handle.write(json.dumps({'id':rows[i]['id'], 'split':split, 'group':int(groups[i]), 'label':rows[i]['label'], 'topic':rows[i]['source_topic']})+'\n')
    with (reports / 'test_predictions.jsonl').open('w', encoding='utf-8') as handle:
        for j,i in enumerate(test):
            handle.write(json.dumps({'id':rows[i]['id'], 'true_scam':int(y[i]), 'predicted_scam':int(pred[j]), 'score':float(test_scores[j]), 'rule_scam':int(rule_pred[j])})+'\n')
    output = ROOT / 'artifacts/models'
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model':model, 'threshold':threshold, 'features':['transcript','ocr_text'], 'license':report['license']}, output / 'binary_baseline.joblib')
    print(json.dumps({key:report[key] for key in ['rows','split','validation_macro_f1','test','rules_test_same_records']}, indent=2))


if __name__ == '__main__':
    main()
