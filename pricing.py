"""
Valuation logic for CarValue.

This module calculates an independent estimated vehicle value using:
- Original vehicle price
- Vehicle age
- Mileage
- Vehicle type
- Vehicle condition

Real market-value data is handled separately through the MarketCheck API.
The internal estimate can then be compared with MarketCheck data in the
results page.
"""

# --------------------------------------------------
# Depreciation assumptions
# --------------------------------------------------

# Estimated annual depreciation rates by vehicle type.
#
# These are internal model assumptions, not live market values.
# MarketCheck provides the external market comparison.
ANNUAL_DEPRECIATION_RATE = {
    "sedan": 0.12,
    "suv": 0.10,
    "truck": 0.09,
    "luxury": 0.15,
}


# Adjustment based on vehicle condition.
CONDITION_FACTOR = {
    "excellent": 1.06,
    "good": 1.00,
    "fair": 0.88,
    "poor": 0.72,
}


# Expected average annual mileage.
EXPECTED_MILES_PER_YEAR = 12000

# Penalty applied to mileage above expected mileage.
EXCESS_MILEAGE_PENALTY = 0.05


def estimate_value(
    price,
    age,
    mileage,
    vehicle_type,
    condition,
):
    """
    Calculate our independent estimated vehicle value.

    The calculation happens in three stages:

    1. Apply annual depreciation based on vehicle type.
    2. Penalize mileage above expected mileage.
    3. Adjust the result based on vehicle condition.
    """

    depreciation_rate = ANNUAL_DEPRECIATION_RATE.get(
        vehicle_type,
        0.12,
    )

    condition_factor = CONDITION_FACTOR.get(
        condition,
        1.00,
    )

    # ----------------------------------------------
    # Age depreciation
    # ----------------------------------------------

    age_adjusted_value = price * (
        (1 - depreciation_rate) ** age
    )

    age_loss = price - age_adjusted_value

    # ----------------------------------------------
    # Mileage adjustment
    # ----------------------------------------------

    expected_mileage = age * EXPECTED_MILES_PER_YEAR

    excess_mileage = max(
        0,
        mileage - expected_mileage,
    )

    mileage_penalty = (
        excess_mileage * EXCESS_MILEAGE_PENALTY
    )

    value_after_mileage = max(
        0,
        age_adjusted_value - mileage_penalty,
    )

    # ----------------------------------------------
    # Condition adjustment
    # ----------------------------------------------

    estimated_value = (
        value_after_mileage * condition_factor
    )

    # Never estimate the car above its original price.
    estimated_value = min(
        estimated_value,
        price,
    )

    total_loss = price - estimated_value

    return {
        "estimated_value": round(estimated_value),
        "age_loss": round(age_loss),
        "mile_loss": round(mileage_penalty),
        "total_loss": round(total_loss),
        "expected_mileage": round(expected_mileage),
        "excess_mileage": round(excess_mileage),
    }


def build_price_variants(estimated_value):
    """
    Create rough selling-price scenarios from our estimate.

    These are model-generated scenarios, not live dealer quotes.
    """

    return {
        "private_party": round(estimated_value),
        "trade_in": round(estimated_value * 0.88),
        "dealer_retail": round(estimated_value * 1.15),
    }


def build_breakdown(
    price,
    age,
    mileage,
    age_loss,
    mile_loss,
    estimated_value,
):
    """
    Build information used to explain the valuation.
    """

    retain_pct = (
        round((estimated_value / price) * 100)
        if price
        else 0
    )

    return {
        "price": round(price),
        "age": age,
        "mileage": mileage,
        "age_loss": age_loss,
        "mile_loss": mile_loss,
        "retain_pct": retain_pct,
    }


def build_recommendation(
    retain_pct,
    mileage,
):
    """
    Generate a simple recommendation from our internal model.

    This is not yet based on live MarketCheck data.
    """

    if retain_pct >= 55 and mileage < 100000:
        return {
            "tone": "sell",
            "action": "Strong Value",
            "reasoning": (
                "Your vehicle has retained a relatively strong "
                "percentage of its original value based on its "
                "age, mileage, and condition."
            ),
        }

    if retain_pct >= 35:
        return {
            "tone": "hold",
            "action": "Moderate Value",
            "reasoning": (
                "Your vehicle has experienced moderate depreciation. "
                "Compare this estimate with the current market value "
                "before deciding whether to sell."
            ),
        }

    return {
        "tone": "wait",
        "action": "High Depreciation",
        "reasoning": (
            "Your vehicle has lost a significant portion of its "
            "original value based on its age, mileage, and condition. "
            "Check the current market value before making a selling "
            "decision."
        ),
    }


def build_full_valuation(
    make,
    model,
    vehicle_type,
    condition,
    price,
    age,
    mileage,
):
    """
    Run the internal CarValue valuation pipeline.

    MarketCheck data is retrieved separately in app.py.
    """

    calc = estimate_value(
        price=price,
        age=age,
        mileage=mileage,
        vehicle_type=vehicle_type,
        condition=condition,
    )

    estimated_value = calc["estimated_value"]

    price_variants = build_price_variants(
        estimated_value
    )

    breakdown = build_breakdown(
        price=price,
        age=age,
        mileage=mileage,
        age_loss=calc["age_loss"],
        mile_loss=calc["mile_loss"],
        estimated_value=estimated_value,
    )

    recommendation = build_recommendation(
        retain_pct=breakdown["retain_pct"],
        mileage=mileage,
    )

    return {
        "estimated_value": estimated_value,
        "price_variants": price_variants,
        "breakdown": breakdown,
        "recommendation": recommendation,
    }