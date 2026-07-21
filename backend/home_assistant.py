import requests


class HomeAssistantError(Exception):
    """Safe error for unavailable Home Assistant controls."""


def _post_service(base_url: str, token: str, service: str, payload: dict) -> None:
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/services/climate/{service}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HomeAssistantError("Home Assistant could not apply the thermostat change.") from exc


def set_temperature(base_url: str, token: str, thermostat: str, celsius: float) -> None:
    _post_service(base_url, token, "set_temperature", {"entity_id": thermostat, "temperature": celsius})


def set_mode(base_url: str, token: str, thermostat: str, mode: str) -> None:
    _post_service(base_url, token, "set_hvac_mode", {"entity_id": thermostat, "hvac_mode": mode})


def get_state(base_url: str, token: str, thermostat: str) -> dict:
    try:
        response = requests.get(
            f"{base_url.rstrip('/')}/api/states/{thermostat}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        attributes = payload.get("attributes", {})
        return {
            "currentTemperature": attributes.get("current_temperature"),
            "targetTemperature": attributes.get("temperature"),
            "mode": payload.get("state"),
        }
    except (requests.RequestException, ValueError) as exc:
        raise HomeAssistantError("Home Assistant could not read the thermostat state.") from exc
