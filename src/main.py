# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request, status
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
# pyrefly: ignore [missing-import]
from fastapi.exceptions import RequestValidationError
from src.routes.bio import router as bio_router
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

app = FastAPI(title="Secure Auth & LLM API")

# Custom exception handler for 400 Bad Request naming the broken field
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field_name = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Invalid input",
            "field": field_name,
            "message": first_error.get("msg", "Validation error")
        }
    )

# Include the new bio extractor router
app.include_router(bio_router)