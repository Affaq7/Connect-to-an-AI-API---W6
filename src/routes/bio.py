import os
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.exceptions import RequestValidationError
from src.llm.schema import BioInput, BioExtractionOutput, RoleCategory

router = APIRouter(prefix="/extract-bio", tags=["LLM Bio Extractor"])

# Hard-coded stub response matching the output schema
STUB_RESPONSE = BioExtractionOutput(
    job_title="Senior Backend Engineer",
    years_experience=5,
    category=RoleCategory.ENGINEERING,
    confidence=0.95
)

@router.post(
    "",
    response_model=BioExtractionOutput,
    status_code=status.HTTP_200_OK,
    summary="Extract structured metadata from profile bio"
)
async def extract_bio(payload: BioInput):
    # Check if Stub Mode is enabled
    is_stub = os.getenv("LLM_STUB", "0") == "1"
    
    if is_stub:
        # Returns immediately without calling any external LLM
        return STUB_RESPONSE
    
    # Placeholder for Stage 2 (real LLM call)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Real LLM pipeline not yet implemented. Set LLM_STUB=1 to test."
    )