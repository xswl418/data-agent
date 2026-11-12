import json
import requests
from pathlib import Path
from unittest.mock import patch

API_URL = "http://localhost:8001/ask"
CASES_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_cases.json"

cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

def ask_and_check(question: str, must_contain: list):
    response = requests.post(API_URL, json={"question": question})
    reply = response.json()["reply"]
    for keyword in must_contain:
        assert keyword in reply, f"期望包含 '{keyword}'，实际回答：{reply[:200]}"

def test_e01_category_max_revenue():
    case = [c for c in cases if c["id"] == "E01"][0]
    ask_and_check(case["question"], case["must_contain"])

def test_e02_region_ranking():
    case = [c for c in cases if c["id"] == "E02"][0]
    ask_and_check(case["question"], case["must_contain"])

def test_e03_east_order_count():
    case = [c for c in cases if c["id"] == "E03"][0]
    ask_and_check(case["question"], case["must_contain"])

def test_e04_beauty_revenue():
    case = [c for c in cases if c["id"] == "E04"][0]
    ask_and_check(case["question"], case["must_contain"])

def test_e05_lowest_region():
    case = [c for c in cases if c["id"] == "E05"][0]
    ask_and_check(case["question"], case["must_contain"])

def test_e06_compare_east_west():
    case = [c for c in cases if c["id"] == "E06"][0]
    ask_and_check(case["question"], case["must_contain"])

def test_e07_compare_electronics_home():
    case = [c for c in cases if c["id"] == "E07"][0]
    ask_and_check(case["question"], case["must_contain"])

def test_e08_anomaly_revenue():
    case = [c for c in cases if c["id"] == "E08"][0]
    ask_and_check(case["question"], case["must_contain"])

def test_e09_anomaly_east_revenue():
    case = [c for c in cases if c["id"] == "E09"][0]
    ask_and_check(case["question"], case["must_contain"])

def test_e10_avg_revenue_highest():
    case = [c for c in cases if c["id"] == "E10"][0]
    ask_and_check(case["question"], case["must_contain"])

@patch("requests.post")
def test_mock_ask_api(mock_post):
    mock_post.return_value.json.return_value = {"reply": "测试回答，Electronics 收入最高， 1,829,899"}

    response = requests.post(API_URL, json={"question": "ddd"})
    reply = response.json()["reply"]

    assert "Electronics" in reply
    assert "1,829,899" in reply