import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SCAMRADAR_RATE_LIMIT_STORAGE", "memory")
os.environ.setdefault("SCAMRADAR_DATABASE_URL", "sqlite://")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app


def main() -> None:
    target = None
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    schema = app.openapi()
    text = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if target is None:
        sys.stdout.write(text)
        return
    target.write_text(text, encoding="utf-8")
    print("wrote " + str(target))


if __name__ == "__main__":
    main()
