# Cisco Catalyst Center Device Monitoring API

A Python backend built with **FastAPI** that retrieves Cisco Catalyst Center network-device inventory and exposes simple REST endpoints for listing devices, filtering by reachability, and looking up a device by hostname.

**Designed for two modes:** **Live mode** integrates with the Cisco DevNet Catalyst Center sandbox; **Demo mode** reads a local JSON fixture so the API can be demonstrated without Cisco credentials, an active sandbox reservation, or internet connectivity.

> **Project status:** The live API, endpoint tests, and Docker workflow were exercised during development. Offline demo mode is an optional extension described below; verify that `demo_client.py`, `data/demo_devices.json`, and the Dockerfile changes are present before claiming the offline demo works. This is an educational portfolio project, not a production monitoring system or an official Cisco product.

## Features

- Fetches Catalyst Center device inventory using `/dna/intent/api/v1/network-device`.
- Authenticates via `/dna/system/api/v1/auth/token` and uses `X-Auth-Token` for subsequent requests.
- Reuses an API client and exposes a dependency through FastAPI `Depends()`.
- Exposes device listing, reachability filtering, and hostname lookup.
- Handles network exceptions and upstream failures, including timeout errors.
- Logs important events without deliberately logging passwords or tokens.
- Uses Pytest, FastAPI TestClient, and mocked dependencies for repeatable endpoint tests.
- Runs locally or in Docker.
- **Optional demo mode:** switches the device-data source from Cisco to a local fixture without changing API endpoints.

## Architecture

```text
                  Browser / Postman / Swagger UI
                              |
                       GET /devices
                              |
                           FastAPI
                              |
                  get_catalyst_client()
                       /           \
               APP_MODE=live    APP_MODE=demo
                    |                 |
              CatalystClient    DemoCatalystClient
                    |                 |
        Cisco Catalyst Center   data/demo_devices.json
              REST API           (synthetic data)
```

The two clients share the expected `get_devices()` interface. FastAPI's dependency-injection mechanism makes the data source replaceable; tests can also override it with a mock.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Simple application status message (not a dependency health check) |
| `GET` | `/devices` | List devices and their status |
| `GET` | `/devices?status=Reachable` | List only reachable devices |
| `GET` | `/devices?status=Unreachable` | List only unreachable devices |
| `GET` | `/devices/{hostname}` | Get one device; returns `404` if no match |
| `GET` | `/docs` | Interactive Swagger/OpenAPI documentation |

**Illustrative response to `GET /devices`:**

```json
{
  "total": 1,
  "devices": [
    {
      "hostname": "sw1",
      "ip": "10.10.20.175",
      "status": "Reachable",
      "type": "Cisco Catalyst 9000 Virtual Switch"
    }
  ]
}
```

Responses vary with the active data source. Data in demo mode is intentionally synthetic and **must not** be described as live network telemetry.

## Requirements

- Python 3.11
- Conda (optional)
- Docker Desktop (optional)
- For **live mode only**: access to an available Cisco DevNet Catalyst Center sandbox and its current credentials

## Quick start: Offline demo (recommended for interviews)

> **Prerequisite:** Implement the `DemoCatalystClient` described below and include `data/demo_devices.json`. If those files have not been added to your local project, offline mode is **not yet available**.

```bash
conda create -n cisco-api python=3.11 -y
conda activate cisco-api
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `APP_MODE=demo` in `.env`. Then run:

```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` and try `/devices`, `/devices?status=Unreachable`, and `/devices/sw1`.

### Demo mode implementation contract

`demo_client.py` should provide `DemoCatalystClient.get_devices()` that reads `data/demo_devices.json` and returns a list of records using the same keys as the Catalyst Center response, such as `hostname`, `managementIpAddress`, `reachabilityStatus`, `type`, `softwareVersion`, and `role`.

In `app.py`, the `get_catalyst_client()` dependency selects `DemoCatalystClient()` when `APP_MODE=demo` and `CatalystClient(...)` when `APP_MODE=live`. Reject unrecognized modes instead of silently selecting live mode. Since the dependency is cached with `@lru_cache`, restart the server after changing `APP_MODE`.

A demo fixture may intentionally include an **unreachable** switch to illustrate filtering. Label it as a simulated test scenario, not a real Cisco incident.

## Live Catalyst Center mode

1. Start or renew your sandbox session on the Cisco DevNet portal.
2. Check the **current** sandbox URL and credentials; these can change.
3. Create `.env` from `.env.example` and set:

```dotenv
APP_MODE=live
CATALYST_URL=https://sandboxdnac.cisco.com
CATALYST_USERNAME=your_sandbox_username
CATALYST_PASSWORD=your_sandbox_password
CATALYST_VERIFY_SSL=true
```

4. Run the FastAPI server and open `/docs` or `/devices`.

If the trusted training sandbox has a self-signed or otherwise untrusted certificate, you may **temporarily** set `CATALYST_VERIFY_SSL=false` for this sandbox only. This disables server-certificate verification and is **insecure**. Production use must validate TLS certificates with an appropriate trust chain.

The sandbox is external and time-limited; live mode may fail if its session expires or the service is unavailable.

## Docker

Ensure your `Dockerfile` copies the optional offline files into the image if you have implemented demo mode:

```dockerfile
COPY app.py catalyst_client.py demo_client.py logging_config.py ./
COPY data/ ./data/
```

> If demo mode is not implemented yet, adjust the `COPY` instructions to match the files that actually exist. The base image, installation steps, and startup command should remain in your existing Dockerfile.

Build once:

```bash
docker build -t cisco-device-api:1.0 .
```

**Offline demo, no credential file needed:**

```bash
docker run --rm --name cisco-device-api \
  -p 127.0.0.1:8000:8000 \
  -e APP_MODE=demo \
  cisco-device-api:1.0
```

**Live sandbox:**

```bash
docker run --rm --name cisco-device-api \
  -p 127.0.0.1:8000:8000 \
  --env-file .env \
  cisco-device-api:1.0
```

Run only one container with that name and port at a time. Visit `http://127.0.0.1:8000/docs` after the container starts.

## Tests

```bash
python -m pytest -v
python -m pytest --cov=app --cov=catalyst_client --cov-report=term-missing
```

Existing endpoint tests use mocked clients, so they do not need the sandbox. **Before treating demo mode as verified**, add a test that loads the JSON fixture and endpoint tests for both `Reachable` and `Unreachable` filters; also check the Docker demo run. Direct `CatalystClient` tests should cover initial authentication, a rejected token followed by one retry, timeouts, invalid upstream data, and HTTP errors. Do not claim a coverage percentage unless you have measured it.

## Five-minute interview demo

1. **30 seconds:** Introduce the goal, technologies, and what Catalyst Center provides.
2. **45 seconds:** Explain the architecture and live versus synthetic data source.
3. **75 seconds:** Open `/docs` and call `/devices`, `/devices?status=Unreachable`, and `/devices/sw1`.
4. **60 seconds:** Open `catalyst_client.py` and `app.py` to explain token authentication, reusable clients, error handling, and dependency injection.
5. **45 seconds:** Run `python -m pytest -v` and explain mocking.
6. **45 seconds:** Show the Docker run and summarize trade-offs or improvements.

If the sandbox is available, you can switch to `APP_MODE=live` for a real integration demo. **Never present demo-fixture results as live results.** Keep credentials, tokens, and `.env` out of screen sharing.

## Suggested project structure

```text
cisco-catalyst-device-monitoring-api/
├── app.py
├── catalyst_client.py
├── demo_client.py             # Required for offline demo mode
├── logging_config.py
├── data/
│   └── demo_devices.json     # Synthetic demo data
├── tests/
│   ├── __init__.py
│   └── test_app.py
├── Dockerfile
├── .dockerignore
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Security, limitations, and next steps

- Keep `.env` and tokens out of source control; use `.env.example` only for placeholder configuration.
- Never disable TLS verification outside a trusted sandbox exercise.
- Add pagination or other inventory iteration for large Catalyst Center installations.
- Make token caching and `requests.Session` usage concurrency-safe before high-load deployment.
- Secure the FastAPI endpoints if exposing the app beyond localhost.
- Add client-specific tests, validated error responses, health checks, and CI.
- The current application is an **inventory/reachability viewer**, not a historical time-series monitoring or alerting platform.

## Technologies

Python 3.11, FastAPI, Requests, Uvicorn, Pytest, HTTPX, Docker, Cisco Catalyst Center REST APIs.

## Disclaimer

Independent educational portfolio project using the Cisco DevNet sandbox. Not an official Cisco product or endorsed by Cisco. Cisco and Catalyst Center are trademarks of Cisco Systems, Inc.
