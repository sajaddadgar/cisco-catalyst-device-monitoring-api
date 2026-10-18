
import logging

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class CatalystClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token = None

        self.session = requests.Session()
        self.session.verify = verify_ssl

    def get_token(self):
        """Get a new authentication token."""

        logger.info("Authenticating with Catalyst Center")

        response = self.session.post(
            f"{self.base_url}/dna/system/api/v1/auth/token",
            auth=HTTPBasicAuth(
                self.username,
                self.password,
            ),
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict) or not isinstance(
            data.get("Token"), str
        ) or not data["Token"]:
            raise ValueError("Invalid authentication response")

        self.token = data["Token"]

        logger.info("Authentication successful")

        return self.token

    def get_devices(self):
        """Get devices, retrying once if the token is rejected."""

        if self.token is None:
            self.get_token()

        url = (
            f"{self.base_url}"
            "/dna/intent/api/v1/network-device"
        )

        logger.info("Requesting network devices")

        response = self.session.get(
            url,
            headers={"X-Auth-Token": self.token},
            timeout=15,
        )

        if response.status_code == 401:
            logger.warning(
                "Token rejected. Re-authenticating once."
            )

            self.get_token()

            response = self.session.get(
                url,
                headers={"X-Auth-Token": self.token},
                timeout=15,
            )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict) or not isinstance(
            data.get("response"), list
        ):
            raise ValueError("Invalid device inventory response")

        devices = data["response"]

        logger.info("Retrieved %d network devices", len(devices))

        return devices
