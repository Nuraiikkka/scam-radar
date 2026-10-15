"""Run the locally trained research baseline on UTF-8 text files."""
import argparse
import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.services.ml_classifier import predict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text-file', type=Path, required=True, help='Transcript in UTF-8')
    parser.add_argument('--ocr-file', type=Path)
    args = parser.parse_args()
    transcript = args.text_file.read_text(encoding='utf-8')
    ocr = args.ocr_file.read_text(encoding='utf-8') if args.ocr_file else ''
    text = ' '.join((transcript + ' ' + ocr).split())
    if len(text) < 40:
        parser.error('Insufficient text: at least 40 characters required')
    print(json.dumps(predict(transcript, ocr, enabled=True), indent=2))


if __name__ == '__main__':
    main()
