import os
import re
import db as db
import pricing

from market_api import MarketAPIError, get_market_value
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set."
    )
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
db.init_db()
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAKES = [
    "Toyota",
    "Honda",
    "Ford",
    "Chevrolet",
    "BMW",
    "Mercedes-Benz",
    "Tesla",
    "Mazda",
    "Subaru",
    "Jeep",
]


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def _to_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@app.route("/")
def home():
    return render_template("home.html", active_page="home")


@app.route("/evaluate")
@login_required
def evaluate():
    return render_template(
        "evaluate.html",
        active_page="evaluate",
        makes=MAKES,
    )

@app.route("/calculate", methods=["POST"])
@login_required
def calculate():
    # -----------------------------
    # 1. Get form data
    # -----------------------------
    make = request.form.get("make", "").strip()
    model = request.form.get("model", "").strip()
    vehicle_type = request.form.get("vehicle_type", "").strip().lower()
    condition = request.form.get("condition", "").strip().lower()

    vin = request.form.get("vin", "").strip().upper()
    zip_code = request.form.get("zip_code", "").strip()

    # -----------------------------
    # 2. Validate text fields
    # -----------------------------
    if not make or not model:
        flash("Please select both the make and model.", "error")
        return redirect(url_for("evaluate"))

    if make not in MAKES:
        flash("Please select a valid vehicle make.", "error")
        return redirect(url_for("evaluate"))

    if vehicle_type not in pricing.ANNUAL_DEPRECIATION_RATE:
        flash("Please select a valid vehicle type.", "error")
        return redirect(url_for("evaluate"))

    if condition not in pricing.CONDITION_FACTOR:
        flash("Please select a valid vehicle condition.", "error")
        return redirect(url_for("evaluate"))

    # -----------------------------
    # 3. Validate VIN + ZIP
    # -----------------------------
    if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin):
        flash("Please enter a valid 17-character VIN.", "error")
        return redirect(url_for("evaluate"))

    if not re.fullmatch(r"\d{5}", zip_code):
        flash("Please enter a valid 5-digit ZIP code.", "error")
        return redirect(url_for("evaluate"))

    # -----------------------------
    # 4. Validate numeric fields
    # -----------------------------
    try:
        price = float(request.form.get("price", ""))
        age = int(request.form.get("age", ""))
        mileage = int(request.form.get("mileage", ""))
    except (TypeError, ValueError):
        flash(
            "Please enter valid numbers for price, age, and mileage.",
            "error",
        )
        return redirect(url_for("evaluate"))

    if price < 500 or price > 1_000_000:
        flash(
            "Original price must be between $500 and $1,000,000.",
            "error",
        )
        return redirect(url_for("evaluate"))

    if age < 0 or age > 50:
        flash(
            "Vehicle age must be between 0 and 50 years.",
            "error",
        )
        return redirect(url_for("evaluate"))

    if mileage < 0 or mileage > 1_000_000:
        flash(
            "Mileage must be between 0 and 1,000,000 miles.",
            "error",
        )
        return redirect(url_for("evaluate"))
    # -----------------------------
    # 5. Run our valuation model
    # -----------------------------
    valuation = pricing.build_full_valuation(
        make=make,
        model=model,
        vehicle_type=vehicle_type,
        condition=condition,
        price=price,
        age=age,
        mileage=mileage,
    )

    # -----------------------------
    # 6. Get MarketCheck value
    # -----------------------------
    try:
        market_data = get_market_value(
            vin=vin,
            mileage=mileage,
            zip_code=zip_code,
        )

    except MarketAPIError as exc:
        # MarketCheck failing should not break our valuation.
        app.logger.warning(
            "MarketCheck request failed: %s",
            exc,
        )

        market_data = {
            "market_price": None,
            "msrp": None,
            "source": None,
        }

    # -----------------------------
    # 7. Save valuation
    # -----------------------------
 
    db.save_valuation(
    user_id=session["user_id"],
    make=make,
    model=model,
    vehicle_type=vehicle_type,
    price=price,
    age=age,
    mileage=mileage,
    estimated_value=valuation["estimated_value"],
    )
    
    recent_queries = db.get_recent_valuations(
    user_id=session["user_id"],
    limit=5,
    )


    # -----------------------------
    # 8. Show results
    # -----------------------------
    return render_template(
        "results.html",
        active_page="results",

        value=valuation["estimated_value"],
        price_variants=valuation["price_variants"],
        breakdown=valuation["breakdown"],
        recommendation=valuation["recommendation"],

        market_value=market_data["market_price"],
        market_msrp=market_data["msrp"],
        market_source=market_data["source"],

        vehicle={
            "make": make,
            "model": model,
            "age": age,
            "mileage": mileage,
            "vehicle_type": vehicle_type,
            "condition": condition,
            "vin": vin,
            "zip_code": zip_code,
        },

        recent_queries=recent_queries,
    )
@app.route("/results")
@login_required
def results():
    # No submitted vehicle to show a valuation for — send them to the form
    # instead of rendering stale/fake numbers.
    flash("Run an estimate first to see your results.", "error")
    return redirect(url_for("evaluate"))


@app.route("/history")
@login_required
def history():
    queries = db.get_recent_valuations(
        user_id=session["user_id"],
        limit=20,
    )

    return render_template(
        "history.html",
        active_page="history",
        queries=queries,
    )

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in every field.", "error")
        elif not EMAIL_RE.match(email):
            flash("That email address doesn't look right.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif password != confirm_password:
            flash("Passwords don't match.", "error")
        elif db.get_user_by_email(email):
            flash("An account with that email already exists.", "error")
        else:
            db.create_user(name, email, generate_password_hash(password))
            user = db.get_user_by_email(email)
            session["user_id"] = user["id"]
            session["user"] = user["name"]
            flash("Account created — welcome to CarValue!", "success")
            return redirect(url_for("evaluate"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    next_url = request.values.get("next") or url_for("home")

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.get_user_by_email(email)

        # Same generic message whether the email or password was wrong —
        # don't leak which one, so accounts can't be enumerated.
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.", "error")
        else:
            session["user_id"] = user["id"]
            session["user"] = user["name"]
            flash("Signed in successfully.", "success")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("home")
            return redirect(next_url)

    return render_template("login.html", next_url=next_url)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You've been logged out.", "success")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run()