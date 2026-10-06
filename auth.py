import os
import threading
import webbrowser
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request
from genai_helper import generate_narrative
from utils.depreciation import estimate_value
from utils.ownership import estimate_costs
from utils.recommendations import get_ai_recommendation, get_recommendation
from database import create_table, get_recent_valuations, save_valuation

app = Flask(__name__)
create_table()


@app.route("/", methods=["GET"])
def home():
    return render_template("landingpage.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    make = request.form["make"]
    model = request.form["model"]
    price = float(request.form["price"])
    age = int(request.form["age"])
    mileage = int(request.form["mileage"])
    vehicle_type = request.form["vehicle_type"]

    value = estimate_value(price, age, mileage, vehicle_type)
    costs = estimate_costs(12000)
    ai_recommendation = get_ai_recommendation(age, mileage, price, value)
    recommendation = get_recommendation(age, mileage, estimated_value=value, price=price)
    if ai_recommendation:
        recommendation = {
            "action": ai_recommendation.split("Action:", 1)[1].split("Reasoning:", 1)[0].strip(),
            "reasoning": ai_recommendation.split("Reasoning:", 1)[1].strip(),
        }
    narrative = generate_narrative(make, model, age, mileage, price, value)

    save_valuation(
        make=make,
        model=model,
        vehicle_type=vehicle_type,
        price=price,
        age=age,
        mileage=mileage,
        estimated_value=value,
    )
    recent_queries = get_recent_valuations(limit=5)

    return render_template(
        "results.html",
        value=value,
        costs=costs,
        recommendation=recommendation,
        narrative=narrative,
        recent_queries=recent_queries,
    )


@app.route("/history")
def history():
    queries = get_recent_valuations(limit=20)
    return render_template("history.html", queries=queries)

@app.route("/evaluate")
def evaluate():
    return render_template("index.html")


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == "__main__":
    # Avoid opening two tabs when debug=True triggers the reloader
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1, open_browser).start()
    app.run(debug=True)