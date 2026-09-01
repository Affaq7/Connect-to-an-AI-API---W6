from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class RoleCategory(str, Enum):
    ENGINEERING = "engineering"
    DESIGN = "design"
    PRODUCT = "product"
    OTHER = "other"

class BioInput(BaseModel):
    """Input payload validation."""
    text: str = Field(..., min_length=1, max_length=1000, description="User profile bio text")

class BioExtractionOutput(BaseModel):
    """Output schema matching the job card contract."""
    job_title: Optional[str] = Field(None, description="Extracted professional title")
    years_experience: Optional[int] = Field(None, ge=0, description="Years of experience if specified")
    category: RoleCategory = Field(..., description="Role category from closed enum list")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")