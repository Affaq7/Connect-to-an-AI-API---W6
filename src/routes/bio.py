import os
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, status
from src.llm.schema import BioInput, BioExtractionOutput, RoleCategory
# pyrefly: ignore [missing-import]
from openai import OpenAI
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/extract-bio", tags=["LLM Bio Extractor"])

# Initialize the client (picks up LLM_BASE_URL and LLM_API_KEY from .env)
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
    """Loads the versioned prompt from the file system."""
    prompt_path = os.path.join(os.getcwd(), "prompts", "extract-bio-v1.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

@router.post(
    "",
    summary="Extract structured metadata from profile bio"
)
async def extract_bio(payload: BioInput):
    is_stub = os.getenv("LLM_STUB", "0") == "1"
    
    if is_stub:
        return STUB_RESPONSE
    
    # 1. Load the system prompt
    system_prompt = load_prompt()
    
    # 2. Call the LLM (Low temperature for consistency)
    response = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL", "openrouter/free"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload.text}
        ],
        temperature=0.0
    )
    
    # 3. Return the raw text for now (We will parse it in Stage 3)
    raw_text = response.choices[0].message.content
    return {"raw_model_output": raw_text}