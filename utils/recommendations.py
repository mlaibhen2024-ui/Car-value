def get_recommendation(age, mileage, estimated_value=None, price=None):
    if age > 10 or mileage > 150000:
        return {
            "action": "Sell the car at this value.",
            "reasoning": (
                "This car is older or has high mileage, so depreciation is likely already cutting into its value. "
                "Selling now can help you avoid extra repair costs and lock in a reasonable return."
            ),
        }

    if age < 5 and mileage < 60000:
        return {
            "action": "Hold on to the car for now.",
            "reasoning": (
                "This car is still fairly young and has relatively low mileage. "
                "If the market stays healthy, waiting a bit longer may let you get more money in the end."
            ),
        }

    return {
        "action": "Watch the market closely.",
        "reasoning": (
            "The car is in a middle ground. It may be worth holding for a little while, but a drop in value "
            "or rising repair costs could make selling sooner the smarter move."
        ),
    }


def get_ai_recommendation(age, mileage, price, estimated_value):
    return None