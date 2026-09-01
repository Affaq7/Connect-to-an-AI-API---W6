# Job card

* **What it does:** Extracts structured professional metadata (job title, experience, and role category) from a messy user-written profile bio.
* **Input:** `{"text": "string, 1-1000 characters"}`
* **Output:** 
  ```json
  {
    "job_title": "string or null",
    "years_experience": "integer or null",
    "category": "one of [engineering|design|product|other]",
    "confidence": "0.0-1.0"
  }
  ```
* **It must never:** invent a category outside the allowed list, guess years of experience if it isn't explicitly mentioned, or return free text outside the JSON.
* **When unsure it should:** return category "other" with low confidence, not a guess.
