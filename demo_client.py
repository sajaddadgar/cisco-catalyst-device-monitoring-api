
import json
from pathlib import Path


class DemoCatalystClient:
    def get_devices(self):
        file_path = (
            Path(__file__).resolve().parent
            / "data"
            / "demo_devices.json"
        )

        with open(file_path, "r") as file:
            return json.load(file)
