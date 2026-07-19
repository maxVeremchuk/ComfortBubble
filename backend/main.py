from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .gemini_service import GeminiParseError, parse_floor_plan
from .models import FloorPlan

settings = get_settings()
app = FastAPI(title="Comfort Bubble floor-plan parser")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

SUPPORTED_TYPES = {"image/png", "image/jpeg"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/floor-plans/parse", response_model=FloorPlan)
async def parse_uploaded_floor_plan(file: UploadFile = File(...)) -> FloorPlan:
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(415, "Upload a PNG or JPEG floor-plan image.")
    content = await file.read()
    if not content:
        raise HTTPException(400, "The uploaded image is empty.")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(413, "The uploaded image exceeds the 10 MB limit.")
    if not settings.gemini_api_key:
        raise HTTPException(503, "Floor-plan analysis is not configured. Set GEMINI_API_KEY.")
    try:
        result = parse_floor_plan(content, file.content_type, settings.gemini_api_key, settings.gemini_model)
    except GeminiParseError as exc:
        raise HTTPException(502, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, "The floor-plan analysis service is temporarily unavailable.") from exc
    if not result.walls and not result.windows:
        raise HTTPException(422, "No walls or windows were detected. Try a clearer floor-plan image.")
    return result
