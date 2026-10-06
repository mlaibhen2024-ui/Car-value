def estimate_value(price, age, mileage, vehicle_type):

    depreciation_rates = {
        "sedan": 0.10,
        "suv": 0.08,
        "truck": 0.07,
        "luxury": 0.15
    }

    rate = depreciation_rates.get(vehicle_type, 0.10)
    value = price

    for _ in range(age):
        value *= (1 - rate)
    value -= mileage * 0.05

    if value < 0:
        value = 0
    return round(value, 2)