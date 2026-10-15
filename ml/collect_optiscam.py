"""Download small JSON records, never the full video/frame archive.

Source license: CC BY-NC-SA 4.0. Keep targets separate from model inputs.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import random
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REF = 'julesgregoryagustin/training-filipino-scam-dataset'
TOPICS = ['crypto', 'ewallet', 'giftcard', 'giveaway', 'p2e', 'task']
VERSION = 6


def download_json(filename, cache):
    path = cache / filename
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    query = urllib.parse.urlencode({'fileName': filename})
    url = f'https://www.kaggle.com/api/v1/datasets/download/{REF}?{query}'
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError('Unexpectedly large metadata record')
            data = json.loads(raw)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            return data
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def convert(record, topic, label, provenance, filename):
    # Never include response, rationale, human_review or the directory label
    # in training text. "human" is title/description, not a human annotation.
    turns = record.get('conversations', [])
    transcript = '\n'.join(t.get('value', '') for t in turns if t.get('from') == 'whisper')
    ocr = '\n'.join(t.get('value', '') for t in turns if t.get('from') == 'ocr')
    metadata = '\n'.join(t.get('value', '') for t in turns if t.get('from') == 'human')
    targets = '\n'.join(t.get('value', '') for t in turns if t.get('from') == 'response')
    import re
    verdict = re.search(r'Scam Verdict:\s*(yes|no|scam|legitimate)\b', targets, re.I)
    if verdict and (verdict.group(1).lower() in {'yes', 'scam'}) != (label == 'scam'):
        raise ValueError('Folder and target verdict disagree')
    return {
        'id': provenance['id'], 'source': REF, 'source_version': VERSION,
        'source_file': filename, 'license': 'CC BY-NC-SA 4.0',
        'label': label, 'source_topic': topic,
        'label_rank': provenance.get('rank', 2),
        'label_provenance': provenance.get('response_source', ''),
        'human_verified': False, 'author_id': None,
        'transcript': transcript, 'ocr_text': ocr, 'metadata_text': metadata,
        'source_record_sha256': hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--per-class-topic', type=int, default=50)
    parser.add_argument('--max-rank', type=int, default=1, choices=[0, 1, 2])
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()
    if args.per_class_topic < 1 or not 1 <= args.workers <= 8:
        parser.error('Positive sample count and 1..8 workers required')
    cache = ROOT / 'data/raw/optiscam'
    # Individual-file endpoint serves current version; fail rather than silently
    # mixing a future version with this audited release.
    with urllib.request.urlopen(f'https://www.kaggle.com/api/v1/datasets/view/{REF}', timeout=30) as response:
        metadata = json.load(response)
    if metadata.get('currentVersionNumber') != VERSION:
        raise ValueError('Dataset version changed; re-audit before collection')
    cache.mkdir(parents=True, exist_ok=True)
    (cache / 'dataset_metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    tasks = []
    manifest_counts = {}
    manifest_errors = []
    rng = random.Random(42)
    for topic in TOPICS:
        try:
            manifest = download_json(f'{topic}/.transfer_manifest.json', cache)
        except Exception as error:
            manifest_errors.append({'topic': topic, 'error': str(error)})
            print(f'Manifest unavailable: {topic}: {error}', flush=True)
            continue
        for label in ['scam', 'legitimate']:
            available = [item for item in manifest[label] if item.get('rank', 2) <= args.max_rank]
            manifest_counts[f'{topic}/{label}'] = len(available)
            rng.shuffle(available)
            for item in available[:args.per_class_topic]:
                video_id = item['id']
                if not all(c.isalnum() or c in '_-' for c in video_id):
                    raise ValueError('Invalid video ID')
                tasks.append((topic, label, item, f'{topic}/{label}/{video_id}/{video_id}.json'))
    print('Eligible per stratum:', json.dumps(manifest_counts), flush=True)
    rows, errors = [], []

    def fetch(task):
        topic, label, item, filename = task
        return convert(download_json(filename, cache), topic, label, item, filename)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(fetch, task): task for task in tasks}
        for n, future in enumerate(as_completed(futures), 1):
            try:
                rows.append(future.result())
            except Exception as error:
                errors.append({'file': futures[future][3], 'error': str(error)})
            if n % 50 == 0 or n == len(tasks):
                print(f'{n}/{len(tasks)} records, {len(errors)} errors', flush=True)
    out = ROOT / 'data/processed'
    out.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda row: (row['source_topic'], row['id']))
    (out / 'optiscam.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows), encoding='utf-8')
    report = {
        'source': f'https://www.kaggle.com/datasets/{REF}', 'version': VERSION,
        'license': 'CC BY-NC-SA 4.0', 'seed': 42,
        'requested_per_class_topic': args.per_class_topic, 'max_rank': args.max_rank,
        'eligible': manifest_counts, 'downloaded': len(rows),
        'labels': dict(Counter(r['label'] for r in rows)),
        'strata': dict(Counter(r['source_topic']+'/'+r['label'] for r in rows)),
        'errors': errors, 'manifest_errors': manifest_errors, 'raw_video_downloaded': False,
        'warning': 'Weak source labels; rank 0 is agentic verification, not confirmed human ground truth.',
    }
    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)
    (reports / 'collection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'downloaded':len(rows), 'errors':len(errors)}), flush=True)


if __name__ == '__main__':
    main()
