import argparse
import csv
import json
import time
import urllib.request
import uuid
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = REPO_DIR / "data" / "samples"


def upload(base_url: str, client_id: str, path: Path) -> str:
    boundary = uuid.uuid4().hex
    head = (
        "--" + boundary + "\r\n"
        'Content-Disposition: form-data; name="file"; filename="' + path.name + '"\r\n'
        "Content-Type: video/mp4\r\n\r\n"
    ).encode()
    tail = ("\r\n--" + boundary + "--\r\n").encode()
    body = head + path.read_bytes() + tail
    request = urllib.request.Request(
        base_url + "/api/v1/analyze",
        data=body,
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary, "X-Client-Id": client_id},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)["analysis_id"]


def wait_for(base_url: str, client_id: str, analysis_id: str) -> dict:
    url = base_url + "/api/v1/analyses/" + analysis_id
    for _ in range(300):
        request = urllib.request.Request(url, headers={"X-Client-Id": client_id})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
        if data["status"] in ("done", "failed"):
            return data
        time.sleep(2)
    raise TimeoutError("analysis " + analysis_id + " did not finish")


def main() -> None:
    parser = argparse.ArgumentParser(description="Send every sample video to a running server")
    parser.add_argument("--base-url", default="http://localhost:8080")
    args = parser.parse_args()
    if not args.base_url.startswith(("http://", "https://")):
        raise SystemExit("--base-url must start with http:// or https://")
    client_id = "samples-" + uuid.uuid4().hex[:12]
    with open(SAMPLES_DIR / "samples.csv", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    print("| Video | Lang | Expected | Actual | Risk | Match | Seconds |")
    print("|---|---|---|---|---|---|---|")
    correct = 0
    for row in rows:
        analysis_id = upload(args.base_url, client_id, SAMPLES_DIR / row["file"])
        data = wait_for(args.base_url, client_id, analysis_id)
        actual = data["category"]
        if actual is None:
            actual = data["error_code"]
        match = "NO"
        if actual == row["category"]:
            match = "yes"
            correct = correct + 1
        risk = "-"
        if data["risk_score"] is not None:
            risk = format(data["risk_score"], ".2f")
        print(
            "| "
            + row["file"]
            + " | "
            + row["lang"]
            + " | "
            + row["category"]
            + " | "
            + str(actual)
            + " | "
            + risk
            + " | "
            + match
            + " | "
            + str(data["processing_seconds"])
            + " |"
        )
    print("")
    print("correct: " + str(correct) + " of " + str(len(rows)))


if __name__ == "__main__":
    main()
