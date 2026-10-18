
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app import app, get_catalyst_client


# Fake devices used only during testing
FAKE_DEVICES = [
    {
        "hostname": "sw1",
        "managementIpAddress": "10.10.20.175",
        "reachabilityStatus": "Reachable",
        "type": "Cisco Virtual Switch",
        "softwareVersion": "17.12.1",
        "role": "ACCESS",
    },
    {
        "hostname": "sw2",
        "managementIpAddress": "10.10.20.176",
        "reachabilityStatus": "Unreachable",
        "type": "Cisco Virtual Switch",
        "softwareVersion": "17.12.1",
        "role": "ACCESS",
    },
]


def test_list_devices():
    # Create a fake Catalyst Center client
    fake_client = Mock()

    # Define what the fake client returns
    fake_client.get_devices.return_value = FAKE_DEVICES

    # Replace FastAPI's real dependency
    app.dependency_overrides[get_catalyst_client] = (
        lambda: fake_client
    )

    try:
        with TestClient(app) as client:
            response = client.get("/devices")

        assert response.status_code == 200
        assert response.json()["total"] == 2
        assert response.json()["devices"][0]["hostname"] == "sw1"

        fake_client.get_devices.assert_called_once()

    finally:
        app.dependency_overrides.clear()



def test_filter_reachable_devices():
    fake_client = Mock()
    fake_client.get_devices.return_value = FAKE_DEVICES

    app.dependency_overrides[get_catalyst_client] = (
        lambda: fake_client
    )

    try:
        with TestClient(app) as client:
            response = client.get(
                "/devices?status=Reachable"
            )

        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["devices"][0]["hostname"] == "sw1"

    finally:
        app.dependency_overrides.clear()




def test_get_device():
    fake_client = Mock()
    fake_client.get_devices.return_value = FAKE_DEVICES

    app.dependency_overrides[get_catalyst_client] = (
        lambda: fake_client
    )

    try:
        with TestClient(app) as client:
            response = client.get("/devices/sw1")

        assert response.status_code == 200
        assert response.json()["hostname"] == "sw1"
        assert response.json()["ip"] == "10.10.20.175"

    finally:
        app.dependency_overrides.clear()





def test_device_not_found():
    fake_client = Mock()
    fake_client.get_devices.return_value = FAKE_DEVICES

    app.dependency_overrides[get_catalyst_client] = (
        lambda: fake_client
    )

    try:
        with TestClient(app) as client:
            response = client.get("/devices/unknown")

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Device 'unknown' not found"
        )

    finally:
        app.dependency_overrides.clear()



import requests


def test_cisco_connection_failure():
    fake_client = Mock()

    fake_client.get_devices.side_effect = (
        requests.exceptions.ConnectionError(
            "Connection failed"
        )
    )

    app.dependency_overrides[get_catalyst_client] = (
        lambda: fake_client
    )

    try:
        with TestClient(app) as client:
            response = client.get("/devices")

        assert response.status_code == 502
        assert response.json()["detail"] == (
            "Unable to connect to Catalyst Center"
        )

    finally:
        app.dependency_overrides.clear()
