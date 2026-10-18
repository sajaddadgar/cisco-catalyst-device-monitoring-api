
import logging
import os
from functools import lru_cache

import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException

from catalyst_client import CatalystClient
from demo_client import DemoCatalystClient


from logging_config import configure_logging


load_dotenv()
configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(title="Cisco Device Monitoring API")


@lru_cache
def get_catalyst_client():
    mode = os.getenv("APP_MODE", "demo").lower()

    if mode == "demo":
        logger.info("Starting in DEMO mode")
        return DemoCatalystClient()

    if mode == "live":
        logger.info("Starting in LIVE mode")
        return CatalystClient(
            base_url=os.environ["CATALYST_URL"],
            username=os.environ["CATALYST_USERNAME"],
            password=os.environ["CATALYST_PASSWORD"],
            verify_ssl=os.getenv(
                "CATALYST_VERIFY_SSL", "true"
            ).lower() == "true",
        )

    raise ValueError(f"Unsupported APP_MODE: {mode}")



def load_devices(client: CatalystClient):
    try:
        return client.get_devices()

    except requests.exceptions.Timeout:
        logger.warning("Catalyst Center request timed out")
        raise HTTPException(
            status_code=504,
            detail="Catalyst Center timed out",
        )

    except requests.exceptions.HTTPError as error:
        status = error.response.status_code

        logger.error(
            "Catalyst Center returned HTTP %d", status
        )

        raise HTTPException(
            status_code=502,
            detail="Catalyst Center returned an error",
        )

    except requests.exceptions.RequestException:
        logger.exception("Catalyst Center connection failed")
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Catalyst Center",
        )

    except (ValueError, KeyError, TypeError):
        logger.exception("Invalid Catalyst Center response")
        raise HTTPException(
            status_code=502,
            detail="Invalid response from Catalyst Center",
        )


@app.get("/")
def home():
    return {
        "message": "Cisco Device Monitoring API is running"
    }


@app.get("/devices")
def list_devices(
    status: str | None = None,
    client: CatalystClient = Depends(get_catalyst_client),
):
    devices = load_devices(client)

    if status is not None:
        devices = [
            device for device in devices
            if device.get("reachabilityStatus", "").lower()
            == status.lower()
        ]

    result = [
        {
            "hostname": d.get("hostname"),
            "ip": d.get("managementIpAddress"),
            "status": d.get("reachabilityStatus"),
            "type": d.get("type"),
        }
        for d in devices
    ]

    return {"total": len(result), "devices": result}


@app.get("/devices/{hostname}")
def get_device(
    hostname: str,
    client: CatalystClient = Depends(get_catalyst_client),
):
    devices = load_devices(client)

    for device in devices:
        if device.get("hostname", "").lower() == hostname.lower():
            return {
                "hostname": device.get("hostname"),
                "ip": device.get("managementIpAddress"),
                "status": device.get("reachabilityStatus"),
                "software": device.get("softwareVersion"),
                "role": device.get("role"),
            }

    raise HTTPException(
        status_code=404,
        detail=f"Device '{hostname}' not found",
    )
