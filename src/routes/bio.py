from pydantic.deprecated import copy_internals
import os
import json
import time
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from src.llm.schema import BioInput, BioExtractionOutput, RoleCategory
# pyrefly: ignore [missing-import]
from openai import OpenAI, APIStatusError, APITimeoutError
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/extract-bio", tags=["LLM Bio Extractor"])

# STAGE 4: Explicit Timeout and Retries
# The SDK uses exponential backoff with jitter by default for 2 retries.
# It automatically retries on 429 and 5xx, but ignores 400, 401, and 403.
client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL"),
    api_key=os.environ.get("LLM_API_KEY"),
    timeout=30.0,
    max_retries=2
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
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    elif cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    return cleaned.strip()

def log_quarantine(payload: BioInput, raw_text: str, error: Exception):
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

# STAGE 4: Cost Logging
def log_cost(model: str, prompt_tokens: int, completion_tokens: int, duration_ms: int, repair_count: int):
    os.makedirs("logs", exist_ok=True)
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": "v1",
        "model": model,
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "duration_ms": duration_ms,
        "repair_count": repair_count
    }
    with open("logs/cost.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

@router.post("", response_model=BioExtractionOutput, summary="Extract structured metadata from profile bio")
async def extract_bio(payload: BioInput):
    # STAGE 4: The Kill Switch
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        return STUB_RESPONSE
        
    if os.getenv("LLM_STUB", "0") == "1":
        return STUB_RESPONSE
    
    system_prompt = load_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": payload.text}
    ]
    
    model_name = os.environ.get("LLM_MODEL", "openrouter/free")
    start_time = time.time()
    repair_count = 0
    prompt_tokens = 0
    completion_tokens = 0
    
    try:
        # ATTEMPT 1
        response = client.chat.completions.create(model=model_name, messages=messages, temperature=0.0)
        
        prompt_tokens += response.usage.prompt_tokens if response.usage else 0
        completion_tokens += response.usage.completion_tokens if response.usage else 0
        raw_text = response.choices[0].message.content
        cleaned_text = clean_llm_json(raw_text)
        
        try:
            result = BioExtractionOutput.model_validate_json(cleaned_text)
        except (ValidationError, ValueError) as e:
            # ATTEMPT 2: Repair
            repair_count = 1
            repair_messages = messages + [
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": f"Your previous answer was rejected for this reason: {str(e)}. Return ONLY corrected JSON matching the schema."}
            ]
            repair_response = client.chat.completions.create(model=model_name, messages=repair_messages, temperature=0.0)
            
            prompt_tokens += repair_response.usage.prompt_tokens if repair_response.usage else 0
            completion_tokens += repair_response.usage.completion_tokens if repair_response.usage else 0
            repair_text = repair_response.choices[0].message.content
            cleaned_repair = clean_llm_json(repair_text)
            
            try:
                result = BioExtractionOutput.model_validate_json(cleaned_repair)
            except (ValidationError, ValueError) as repair_error:
                log_quarantine(payload, repair_text, repair_error)
                raise HTTPException(status_code=422, detail="Unprocessable Entity: LLM failed to return valid schema after repair.")
                
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="Gateway Timeout: LLM provider took too long to respond.")
    except APIStatusError as e:
        raise HTTPException(status_code=e.status_code, detail=f"LLM Provider Error: {e.message}")
    
    finally:
        # Always log the cost, even if it failed midway
        duration_ms = int((time.time() - start_time) * 1000)
        log_cost(model_name, prompt_tokens, completion_tokens, duration_ms, repair_count)
        
    return result