import json
import requests
from pathlib import Path

CASES_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_cases.json"
API_URL = "http://localhost:8001/ask"

def run_eval():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        response = requests.post(url=API_URL, json={"question": case["question"]})
        reply = response.json()["reply"]
        passed = all(kw in reply for kw in case["must_contain"])
        results.append({
            "id": case["id"],
            "passed": passed,
            "question": case["question"],
            "reply": reply,
        })
        status = "✓" if passed else "✗"
        print(f"{status}{case['id']}: {case['question']}")
        if not passed:
            print(f"  期望包含：{case['must_contain']}")
            print(f"  实际回答：{reply[:100]}...")

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\n通过: {passed}/{total}")

if __name__ == "__main__":
    run_eval()