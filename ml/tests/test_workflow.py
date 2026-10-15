import pytest

from ml.collect_optiscam import convert


def test_targets_are_not_training_features():
    record = {
        'conversations': [
            {'from':'whisper', 'value':'Spoken words'},
            {'from':'ocr', 'value':'Visible words'},
            {'from':'human', 'value':'Title and description'},
            {'from':'response', 'value':'Scam Verdict: yes\nWhy Verdict: SECRET_TARGET'},
        ],
        'human_review': {'annotation':'SECRET_TARGET'},
    }
    row = convert(record, 'crypto', 'scam', {'id':'youtube_test', 'rank':0}, 'example.json')
    assert row['transcript'] == 'Spoken words'
    assert row['ocr_text'] == 'Visible words'
    assert row['human_verified'] is False
    assert 'SECRET_TARGET' not in str(row)


def test_disagreement_is_excluded():
    record = {'conversations':[{'from':'response','value':'Scam Verdict: no'}]}
    with pytest.raises(ValueError, match='disagree'):
        convert(record, 'crypto', 'scam', {'id':'test'}, 'example.json')


def test_duplicate_components_cannot_cross_split():
    pytest.importorskip('sklearn')
    from ml.train_baseline import duplicate_groups, split_indices, input_text
    import numpy as np
    rows = []
    # Distinct tokens ensure separate components; copies share content/ID.
    for i in range(50):
        rows.append({'id':f'v{i}', 'transcript':f'Unique document {i} token{i} '*10, 'ocr_text':'', 'author_id':None})
    rows.append(dict(rows[0]))
    texts = [input_text(row) for row in rows]
    groups = duplicate_groups(rows, texts)
    assert groups[0] == groups[-1]
    y = np.array([i % 2 for i in range(50)] + [0])
    train, val, test, _ = split_indices(y, groups, set())
    assert not (set(groups[train]) & set(groups[val]))
    assert not (set(groups[train]) & set(groups[test]))
    assert not (set(groups[val]) & set(groups[test]))


def test_model_inputs_exclude_metadata_and_labels():
    pytest.importorskip('sklearn')
    from ml.train_baseline import input_text
    assert input_text({'transcript':'speech', 'ocr_text':'screen', 'metadata_text':'SECRET', 'label':'scam'}) == 'speech screen'
