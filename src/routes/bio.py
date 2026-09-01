import os
import json
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from src.llm.schema import BioInput, BioExtractionOutput, RoleCategory
# pyrefly: ignore [missing-import]
from openai import OpenAI
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

# We restore response_model to ensure FastAPI serializes the output properly
router = APIRouter(prefix="/extract-bio", tags=["LLM Bio Extractor"])

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL"),
    api_key=os.environ.get("LLM_API_KEY")
)

STUB_RESPONSE = BioExtractionOutput(
    job_title="Senior Backend Engineer",
    years_experience=5,
    category=RoleCategory.ENGINEERING,
    confidence=0.95
)

def load_prompt() -> str:
    prompt_path = os.path.join(os.getcwd(), "prompts", "extract-bio-v1.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def clean_llm_json(raw_text: str) -> str:
    """Strips markdown code fences if the LLM adds them."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def log_quarantine(payload: BioInput, raw_text: str, error: Exception):
    """Logs unrepairable LLM outputs[cite: 2]."""
    os.makedirs("logs", exist_ok=True)
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": payload.text,
        "raw_output": raw_text,
        "error": str(error),
        "prompt_version": "v1"
    }
    with open("logs/quarantine.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

@router.post(
    "",
    response_model=BioExtractionOutput,
    summary="Extract structured metadata from profile bio"
)
async def extract_bio(payload: BioInput):
    is_stub = os.getenv("LLM_STUB", "0") == "1"
    if is_stub:
        return STUB_RESPONSE
    
    system_prompt = load_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": payload.text}
    ]
    
    # ATTEMPT 1
    response = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "openrouter/free"),
        messages=messages,
        temperature=0.0
    )
    raw_text = response.choices[0].message.content
    cleaned_text = clean_llm_json(raw_text)
    
    try:
        # Validate against the Pydantic schema[cite: 2]
        return BioExtractionOutput.model_validate_json(cleaned_text)
    
    except (ValidationError, ValueError) as e:
        # ATTEMPT 2: The Repair Retry[cite: 2]
        repair_messages = messages + [
            {"role": "assistant", "content": raw_text},
            {"role": "user", "content": f"Your previous answer was rejected for this reason: {str(e)}. Return ONLY corrected JSON matching the schema."}
        ]
        
        repair_response = client.chat.completions.create(
            model=os.environ.get("LLM_MODEL", "openrouter/free"),
            messages=repair_messages,
            temperature=0.0
        )
        repair_text = repair_response.choices[0].message.content
        cleaned_repair = clean_llm_json(repair_text)
        
        try:
            return BioExtractionOutput.model_validate_json(cleaned_repair)
        except (ValidationError, ValueError) as repair_error:
            # FAIL CLEANLY[cite: 2]
            log_quarantine(payload, repair_text, repair_error)
            raise HTTPException(
                status_code=422,
                detail="Unprocessable Entity: LLM failed to return valid schema after repair."
            )