# Cisco Catalyst Center Device Monitoring API

A Python backend built with **FastAPI** that retrieves Cisco Catalyst Center network-device inventory and exposes simple REST endpoints for listing devices, filtering by reachability, and looking up a device by hostname.



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


## Quick start: Offline demo


```bash
conda create -n cisco-api python=3.11 -y
conda activate cisco-api
python -m pip install -r requirements.txt

```

Set `.env`:

```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` and try `/devices`, `/devices?status=Unreachable`, and `/devices/sw1`.


## Live Catalyst Center mode

1. Start or renew your sandbox session on the Cisco DevNet portal.
2. Check the **current** sandbox URL and credentials; these can change.
3. `.env`:

```dotenv
APP_MODE=live
CATALYST_URL=https://sandboxdnac.cisco.com
CATALYST_USERNAME=your_sandbox_username
CATALYST_PASSWORD=your_sandbox_password
CATALYST_VERIFY_SSL=true
```

4. Run the FastAPI server and open `/docs` or `/devices`.



## Docker


**Offline demo, (Without any credential):**

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


## Tests

```bash
python -m pytest -v
python -m pytest --cov=app --cov=catalyst_client --cov-report=term-missing
```



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


## Technologies

Python 3.11, FastAPI, Requests, Uvicorn, Pytest, HTTPX, Docker, Cisco Catalyst Center REST APIs.
