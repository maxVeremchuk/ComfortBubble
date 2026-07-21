from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .gemini_service import GeminiParseError, parse_floor_plan
from .home_assistant import HomeAssistantError, get_state, set_mode, set_temperature
from .models import FloorPlan, ThermostatModeRequest, ThermostatState, ThermostatTemperatureRequest

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


def _home_assistant_token() -> str:
    if not settings.home_assistant_token:
        raise HTTPException(503, "Home Assistant control is not configured. Set HOME_ASSISTANT_TOKEN.")
    return settings.home_assistant_token


def _thermostat_entity(number: int) -> str:
    if settings.home_assistant_thermostat_pattern:
        try:
            return settings.home_assistant_thermostat_pattern.format(number=number)
        except KeyError as exc:
            raise HTTPException(500, "HOME_ASSISTANT_THERMOSTAT_PATTERN must include {number}.") from exc
    return settings.home_assistant_thermostat if number == 1 else f"{settings.home_assistant_thermostat}_{number}"


@app.post("/api/thermostat/temperature")
def update_thermostat_temperature(command: ThermostatTemperatureRequest) -> dict[str, str]:
    try:
        set_temperature(settings.home_assistant_url, _home_assistant_token(), _thermostat_entity(command.entityNumber), command.temperature)
    except HomeAssistantError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"status": "ok"}


@app.post("/api/thermostat/mode")
def update_thermostat_mode(command: ThermostatModeRequest) -> dict[str, str]:
    try:
        set_mode(settings.home_assistant_url, _home_assistant_token(), _thermostat_entity(command.entityNumber), command.mode)
    except HomeAssistantError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"status": "ok"}


@app.get("/api/thermostat/state", response_model=ThermostatState)
def read_thermostat_state(entityNumber: int = Query(default=1, ge=1, le=50)) -> ThermostatState:
    try:
        return ThermostatState.model_validate(
            get_state(settings.home_assistant_url, _home_assistant_token(), _thermostat_entity(entityNumber))
        )
    except HomeAssistantError as exc:
        raise HTTPException(502, str(exc)) from exc


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
