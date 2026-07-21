# Comfort Bubble

Comfort Bubble is an interactive thermal digital twin for an apartment. It models a coarse temperature field, lets users edit the floor-plan grid, prioritizes cooling the room occupied by the avatar, and can synchronize the selected temperature and HVAC mode with Home Assistant.

## What it does

- Simulates temperature across a editable grid with diffusion, exterior transfer, windows, walls, AC airflow, and optional heat sources.
- Lets users place and remove walls, windows, doors, ACs, sensors, thermostats, and an avatar.
- Detects the avatar's enclosed room and runs an AC in that room while switching ACs in other rooms off.
- Shows a live time-and-savings benchmark, including a self-correcting ETA derived from observed simulation cooling rates.
- Imports PNG/JPEG floor plans through Gemini and converts validated normalized wall/window geometry into grid cells.
- Integrates with local Home Assistant thermostat entities to prove that the app is working in reality.

The supplied example image is [public/sample-floor-plan.png](public/sample-floor-plan.png).

## Project structure

| Location | Purpose |
| --- | --- |
| `app/page.tsx` | Interactive simulation, layout editor, room logic, UI, and browser-side Home Assistant synchronization. |
| `app/floor-plan-api.ts` | Typed frontend client for the FastAPI backend. |
| `app/*.css` | Simulator, upload, room-label, benchmark, logo, and Home Assistant presentation styles. |
| `backend/main.py` | FastAPI routes, input validation, CORS, and error responses. |
| `backend/gemini_service.py` | Gemini floor-plan analysis and strict response normalization. |
| `backend/home_assistant.py` | Home Assistant REST client for thermostat state and commands. |
| `SIMULATION_FORMULAS.md` | Detailed thermal equations and control logic. |
| `.env.example` | Safe configuration template; copy it to `.env` locally. |

## Simulation model

The model uses a finite-difference grid. It combines open-air diffusion, exterior leakage, accelerated window transfer, small wall conduction, a directional AC plume, and a predictive on/off controller. Read the equations, coefficients, and control thresholds in [SIMULATION_FORMULAS.md](SIMULATION_FORMULAS.md).

The ETA starts from the room area, airflow travel distance, number of ACs, and temperature gap. As the simulation advances, it updates from the measured rate at the avatar and thermostat, so an inaccurate initial estimate converges toward observed behavior. It is a simulation aid, not an engineering-grade HVAC load calculation.

## Requirements

- Node.js 22.13 or later
- Python 3.10 or later for the FastAPI backend
- Optional: a Gemini API key for floor-plan uploads
- Optional: a reachable Home Assistant instance and long-lived access token for real thermostat control (we used Honeywell Home X2S Smart Thermostat)

## Run locally

1. Install frontend dependencies:

   ```bash
   npm install
   ```

2. Create local configuration:

   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and set at least `GEMINI_API_KEY`. Configure Home Assistant values only when you intend to send real thermostat commands.

4. Start the Python backend in one terminal:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   uvicorn backend.main:app --reload --port 8000
   ```

5. Start the frontend in another terminal:

   ```powershell
   npm run dev
   ```

The frontend defaults to `http://localhost:8000` for its API. Change `NEXT_PUBLIC_FLOOR_PLAN_API_URL` in `.env` only if the backend uses a different URL.

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `GEMINI_API_KEY` | For uploads | Gemini key used only by the FastAPI service. |
| `NEXT_PUBLIC_FLOOR_PLAN_API_URL` | No | Backend URL; defaults to `http://localhost:8000`. |
| `HOME_ASSISTANT_URL` | For HA control | Home Assistant URL; defaults to `http://localhost:8123`. |
| `HOME_ASSISTANT_TOKEN` | For HA control | Long-lived Home Assistant token. Never put this in frontend code. |
| `HOME_ASSISTANT_THERMOSTAT` | For one thermostat | Base entity for the first thermostat. |
| `HOME_ASSISTANT_THERMOSTAT_PATTERN` | For multiple thermostats | Numbered template, e.g. `climate.living_room_thermostat_{number}`. |

## Home Assistant integration

Install and configure Home Assistant using the official [Home Assistant installation guide](https://www.home-assistant.io/installation/). Then create a long-lived access token and set the Home Assistant variables in `.env`.

The frontend communicates only with this project's FastAPI backend. The backend calls the Home Assistant REST API, so the access token is never sent to the browser.

- `POST /api/thermostat/temperature` sets a temperature.
- `POST /api/thermostat/mode` sends `cool` or `off`.
- `GET /api/thermostat/state?entityNumber=1` reads the current temperature, target, and HVAC mode.

Grid thermostats are ordered by their placement in the current grid state, not their internal object IDs: first is HA entity 1, second is HA entity 2, and so on. Removing one reindexes the remaining entries. The UI reads the current HA state on page load and every 60 seconds.

> **Caution:** Enabling Home Assistant variables lets the simulator issue real `cool`, `off`, and temperature commands. Test with a non-critical climate entity first.

## Floor-plan upload

Use **Upload floor plan** in the left panel to select a PNG or JPEG up to 10 MB. The image is posted as multipart form data to `POST /api/floor-plans/parse`. Gemini is asked for normalized wall/window geometry; the backend validates the response with Pydantic before the frontend replaces the current editable layout.

## Editing the map

Use the layout tools to place simulation elements. The **Label room** tool creates visual-only room labels; selecting an existing label location edits it, and submitting an empty label removes it. Labels do not affect the simulation.

## Development commands

```bash
npm run dev       # Run the frontend
npm run build     # Production build verification
npm run lint      # Lint frontend sources
python -m pytest backend/tests  # Backend tests, if Python is installed
```

## How Codex and GPT-5.6 helped

This project was developed collaboratively with Codex powered by GPT-5.6. It assisted with implementing the FastAPI/Gemini boundary, typed API clients, simulator interactions, room-based AC control, Home Assistant integration, UI iterations, and documentation. The project owner defines the product behavior, supplies credentials and external systems, and remains responsible for reviewing changes and validating any real HVAC commands before use.

## References

- [Home Assistant installation](https://www.home-assistant.io/installation/)
- [Home Assistant REST API](https://developers.home-assistant.io/docs/api/rest/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Gemini API documentation](https://ai.google.dev/gemini-api/docs)
- [vinext](https://github.com/cloudflare/vinext)
