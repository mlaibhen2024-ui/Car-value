import os

import requests
from dotenv import load_dotenv

load_dotenv()

MARKETCHECK_API_KEY = os.getenv("MARKETCHECK_API_KEY")

MARKETCHECK_PRICE_URL = (
    "https://api.marketcheck.com/v2/predict/car/us/marketcheck_price"
)


class MarketAPIError(Exception):
    """Raised when market-value data cannot be retrieved."""
    pass


def get_market_value(vin, mileage, zip_code, dealer_type="independent"):
    """
    Get a vehicle's predicted market value from MarketCheck.

    Returns:
        {
            "market_price": ...,
            "msrp": ...,
            "source": "MarketCheck"
        }
    """

    if not MARKETCHECK_API_KEY:
        raise MarketAPIError("MARKETCHECK_API_KEY is not configured.")

    vin = vin.strip().upper()
    zip_code = zip_code.strip()

    if len(vin) != 17:
        raise MarketAPIError("VIN must contain exactly 17 characters.")

    if mileage < 0:
        raise MarketAPIError("Mileage cannot be negative.")

    params = {
        "api_key": MARKETCHECK_API_KEY,
        "vin": vin,
        "miles": mileage,
        "dealer_type": dealer_type,
        "zip": zip_code,
    }

    try:
        response = requests.get(
            MARKETCHECK_PRICE_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

    except requests.Timeout:
        raise MarketAPIError("MarketCheck request timed out.")

    except requests.RequestException as exc:
        raise MarketAPIError(
            "Unable to retrieve market value."
        ) from exc

    data = response.json()

    return {
        "market_price": data.get("marketcheck_price"),
        "msrp": data.get("msrp"),
        "source": "MarketCheck",
    }