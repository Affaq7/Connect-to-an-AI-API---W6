import json
import httpx

def run_evals():
    with open("evals/cases.json", "r", encoding="utf-8") as f:
        cases = json.load(f)

    passed = 0
    url = "http://127.0.0.1:8000/extract-bio"

    print(f"Running {len(cases)} evaluation cases...\n")
    for i, case in enumerate(cases, 1):
        response = httpx.post(url, json={"text": case["input"]}, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            predicted_cat = data.get("category")
            expected_cat = case["expected_category"]
            
            if predicted_cat == expected_cat:
                print(f"Case {i}: PASS (Got {predicted_cat})")
                passed += 1
            else:
                print(f"Case {i}: FAIL (Expected {expected_cat}, got {predicted_cat})")
        else:
            print(f"Case {i}: ERROR (Status {response.status_code}: {response.text})")

    print(f"\nFinal Score: {passed}/{len(cases)}")

if __name__ == "__main__":
    run_evals()