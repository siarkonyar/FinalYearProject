import os
import json
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

API_KEY = os.getenv("API_KEY")
HEADERS = {"X-API-Key": API_KEY}


# def fetch_daily_emission(day: str) -> dict:
#     """Fetch network CO2e emission for a specific day (YYYY-MM-DD)."""
#     resp = requests.get("https://api.vechainstats.com/v2/carbon/co2e-network",
#                         params={"timeframe": day}, headers=HEADERS)
#     resp.raise_for_status()
#     return resp.json()


# def fetch_daily_gas_stats(day: str) -> dict:
#     """Fetch network gas limit/used stats for a specific day (YYYY-MM-DD)."""
#     resp = requests.get("https://api.vechainstats.com/v2/network/gas-stats",
#                         params={"timeframe": day}, headers=HEADERS)
#     resp.raise_for_status()
#     return resp.json()


# if __name__ == "__main__":
#     yesterday = (date.today() - timedelta(days=1)).isoformat()

#     print("=== Carbon Emission ===")
#     print(json.dumps(fetch_daily_emission(yesterday), indent=2))

#     print("\n=== Gas Stats ===")
#     print(json.dumps(fetch_daily_gas_stats(yesterday), indent=2))
