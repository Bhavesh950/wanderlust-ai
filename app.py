# ============================
#   IMPORTS & CONFIG
# ============================

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql as sql
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from random import randint
from flask_mail import Mail, Message  
import requests
from datetime import datetime , timedelta , timezone
import re
import json
from functools import wraps
from user_agents import parse
from dotenv import load_dotenv

load_dotenv()




# ============================
#   STATIC DATA / CONSTANTS
# ============================
DESTINATION_DESCRIPTIONS = {
    "jaipur": "Jaipur, the Pink City, is known for its royal palaces, historic forts, vibrant markets, and rich Rajasthani culture.",
    "delhi": "Delhi, the heart of India, blends ancient monuments with modern life, offering history, food, and shopping.",
    "mumbai": "Mumbai, the City of Dreams, is famous for Bollywood, Marine Drive, nightlife, and coastal beauty.",
    "goa": "Goa is known for beaches, nightlife, water sports, seafood, and relaxed vibes.",
    "manali": "Manali is a beautiful hill station known for snow-capped mountains, adventure sports, and scenic valleys.",
}
REAL_DESTINATIONS = {
    "snow": ["Manali", "Shimla", "Kashmir", "Finland", "Iceland"],
    "mountain": ["Manali", "Ladakh", "Swiss Alps", "Nepal"],
    "beach": ["Goa", "Bali", "Maldives", "Phuket"],
    "historical": ["Jaipur", "Delhi", "Rome", "Agra"],
    "city": ["Mumbai", "Dubai", "London", "New York"],
    "nature": ["Kerala", "Bali", "Switzerland", "Banff"]
}
ADMIN_EMAIL = "bhaveshmulchandani651@gmail.com"

def make_slug(text):
    return text.lower().replace(" ", "-").replace(",", "")

# ============================
#   FLASK APP SETUP
# ============================

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.secret_key = "ndjsjdnkjsdknskndskndknas"


# ============================
#   FILE UPLOAD SETTINGS
# ============================


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXT = {"png","jpg","jpeg","gif"}
MAX_CONTENT_LENGTH = 4 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


# ============================
#   DATABASE CONNECTION
# ============================

def get_connection():
    return sql.Connect(
        host="localhost",
        user="root",
        password="RED950rose%",
        db="python",
        port=3306,
        cursorclass=sql.cursors.DictCursor
    )

def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXT


# ============================================================
#   AUTHENTICATION (LOGIN / SIGNUP / LOGOUT / PROFILE)
# ============================================================

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            con = get_connection(); cur = con.cursor()
            cur.execute("SELECT * FROM user WHERE email=%s", (email,))
            if cur.fetchone():
                return render_template("signup.html", fail="Email already exists!")
            hashed = generate_password_hash(password)
            cur.execute("INSERT INTO user (name, email, passwords) VALUES (%s,%s,%s)", (name,email,hashed))
            con.commit()
            return redirect(url_for("login"))
        except Exception as e:
            print("SIGNUP ERROR:", e)
            return render_template("signup.html", fail="Something went wrong!")
        finally:
            try: con.close()
            except: pass
    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email"); password = request.form.get("password")
        try:
            con = get_connection(); cur = con.cursor()
            cur.execute("SELECT * FROM user WHERE email=%s", (email,))
            user = cur.fetchone()
            if not user:
                return render_template("login.html", fail="Invalid email or password!")
            if not check_password_hash(user["passwords"], password):
                return render_template("login.html", fail="Incorrect password!")
            session.permanent = False
            session["user_id"] = user["id"]
            session["user_name"] = user.get("name") or ""
            session["user_email"] = user.get("email")
            session["tab_token"] = str(uuid4())
            avatar_url = url_for('static', filename='images/default-avatar.png')
            if user.get("avatar"):
                avatar_url = url_for('static', filename='uploads/' + user["avatar"])
            session["user_avatar"] = avatar_url
            return redirect(url_for("home"))
        except Exception as e:
            print("LOGIN ERROR:", e)
            return render_template("login.html", fail="Something went wrong!")
        finally:
            try: con.close()
            except: pass
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/profile", methods=["GET","POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        phone_country = request.form.get("phone_country", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        gender = request.form.get("gender", "").strip()
        about = request.form.get("about", "").strip()

        full_name = (first_name + " " + last_name).strip() or session.get("user_name")

        avatar_filename = None
        file = request.files.get("avatar")

        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{user_id}_{uuid4().hex}_{filename}"
            dest = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(dest)
            avatar_filename = filename

        try:
            con = get_connection()
            cur = con.cursor()

            if avatar_filename:
                cur.execute("""
                    UPDATE user 
                    SET name=%s, first_name=%s, last_name=%s,
                        phone_country=%s, phone_number=%s, gender=%s, 
                        about=%s, avatar=%s
                    WHERE id=%s
                """, (full_name, first_name, last_name, phone_country,
                      phone_number, gender, about, avatar_filename, user_id))
            else:
                cur.execute("""
                    UPDATE user 
                    SET name=%s, first_name=%s, last_name=%s,
                        phone_country=%s, phone_number=%s, gender=%s, 
                        about=%s
                    WHERE id=%s
                """, (full_name, first_name, last_name, phone_country,
                      phone_number, gender, about, user_id))

            con.commit()

           
            session["user_name"] = full_name

            if avatar_filename:
                session["user_avatar"] = url_for("static", filename="uploads/" + avatar_filename)
            session.modified = True

            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))

        except Exception as e:
            print("PROFILE UPDATE ERROR:", e)
            flash("Could not update profile.", "danger")
            try:
                con.rollback()
            except:
                pass
        finally:
            try:
                con.close()
            except:
                pass

  
    avatar = url_for("static", filename="images/default-avatar.png")
    user = {}

    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM user WHERE id=%s", (session["user_id"],))
        user = cur.fetchone() or {}

        if user.get("avatar"):
            avatar = url_for("static", filename="uploads/" + user["avatar"])
            session["user_avatar"] = avatar
        else:
            session["user_avatar"] = avatar

        session.modified = True

    except Exception as e:
        print("PROFILE FETCH ERROR:", e)
    finally:
        try:
            con.close()
        except:
            pass

    return render_template("profile.html", user=user, avatar=avatar)


# ----------------------------
#   ACCOUNT SETTINGS
# ----------------------------

@app.route("/settings", methods=["GET","POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    msg = None

    if request.method == "POST":
        action = request.form.get("action")

        
        if action == "delete_account":
            try:
                con = get_connection()
                cur = con.cursor()
                cur.execute("DELETE FROM user WHERE id=%s", (session["user_id"],))
                con.commit()
            except Exception as e:
                print("DELETE ACCOUNT ERROR:", e)
                msg = "Could not delete account."
            finally:
                try: con.close()
                except: pass

            session.clear()
            return redirect(url_for("home"))

        if action == "change_password":
            current = request.form.get("current_password")
            new_pass = request.form.get("new_password")
            confirm_pass = request.form.get("confirm_password")

            
            if new_pass != confirm_pass:
                msg = "New passwords do not match!"
                return render_template("settings.html", msg=msg)

            
            con = get_connection()
            cur = con.cursor()
            cur.execute("SELECT passwords FROM user WHERE id=%s", (session["user_id"],))
            user = cur.fetchone()

            
            if not check_password_hash(user["passwords"], current):
                msg = "Current password is incorrect!"
                return render_template("settings.html", msg=msg)

            
            new_hash = generate_password_hash(new_pass)
            cur.execute("UPDATE user SET passwords=%s WHERE id=%s",
                        (new_hash, session["user_id"]))
            con.commit()
            con.close()

            msg = "Password updated successfully!"
            return render_template("settings.html", msg=msg)

    return render_template("settings.html")

# ============================================================
#   PASSWORD RESET (OTP)
# ============================================================

otp_storage = {}  

@app.route("/send-otp", methods=["POST"])
def send_otp():
    if "user_email" not in session:
        return jsonify({"status": "not_logged_in"})

    otp = randint(100000, 999999)
    session["otp"] = otp
    print("OTP:", otp)

    #  Email function (uncomment if flask-mail configured)
    # msg = Message("Your Password Reset OTP",
    #               sender="your_email@gmail.com",
    #               recipients=[session["user_email"]])
    # msg.body = f"Your OTP is: {otp}"
    # mail.send(msg)

    return jsonify({"status": "sent"})


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    msg = None

    if request.method == "POST":
        email = request.form.get("email")

        con = get_connection()
        cur = con.cursor()
        cur.execute("SELECT id FROM user WHERE email=%s", (email,))
        user = cur.fetchone()
        con.close()

        if not user:
            msg = "Email not found!"
        else:
            otp = randint(100000, 999999)
            session["fp_email"] = email
            session["fp_otp"] = otp

            print("OTP SENT:", otp)

            msg = "OTP sent to your email!"

    return render_template("forgot_password.html", msg=msg)

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    email = request.form.get("email")
    otp = request.form.get("otp")

    if "fp_email" not in session or "fp_otp" not in session:
        return redirect("/forgot-password")

    if email != session["fp_email"]:
        return render_template("forgot_password.html", msg="Invalid email!")

    if str(otp) != str(session["fp_otp"]):
        return render_template("forgot_password.html", msg="Wrong OTP!")

    session["reset_email"] = email
    return redirect("/reset-password")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    msg = None

    if request.method == "POST":
        new_pass = request.form.get("new_password")
        confirm_pass = request.form.get("confirm_password")

        if new_pass != confirm_pass:
            msg = "Passwords do not match!"
            return render_template("reset_password.html", msg=msg)

        email = session.get("reset_email")
        if not email:
            return redirect("/forgot-password")

        con = get_connection()
        cur = con.cursor()

        hashed = generate_password_hash(new_pass)

        cur.execute("UPDATE user SET passwords=%s WHERE email=%s",
                    (hashed, email))
        con.commit()
        con.close()

        otp_storage.pop(email, None)
        session.pop("reset_email", None)

        return redirect("/login")

    return render_template("reset_password.html")

@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    email = session.get("fp_email")
    if not email:
        return redirect("/forgot-password")

    otp = randint(100000, 999999)
    session["fp_otp"] = otp

    print("RESEND OTP:", otp)

    return render_template("forgot_password.html", msg="New OTP sent!")

# ============================================================
#   USER TRIPS (SAVE / DELETE / DETAILS / MY TRIPS)
# ============================================================

@app.route('/my-trips')
def my_trips():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        con = get_connection()
        cur = con.cursor()

        cur.execute("SELECT * FROM saved_trips WHERE user_id = %s", (session['user_id'],))
        trips = cur.fetchall()
        print("DEBUG TRIPS:", trips)
        for trip in trips:
            trip["slug"] = make_slug(trip["title"])

    except Exception as e:
        print("ERROR LOADING TRIPS:", e)
        trips = []
    finally:
        try:
            con.close()
        except:
            pass

    return render_template('my_trips.html', trips=trips)


@app.route("/saved-trips", endpoint="saved_trips")
def saved_trips():
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        con = get_connection()
        cur = con.cursor()

        cur.execute("SELECT * FROM saved_trips WHERE user_id = %s", (session['user_id'],))
        trips = cur.fetchall()

        for trip in trips:
            trip["slug"] = make_slug(trip["title"])

    except Exception as e:
        print("LOAD SAVED TRIPS ERROR:", e)
        trips = []

    finally:
        try:
            con.close()
        except:
            pass

    return render_template("saved_places.html", trips=trips)

@app.route("/my-trips/details/<int:trip_id>")
def trip_details(trip_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        con = get_connection()
        cur = con.cursor()

        cur.execute("""
            SELECT * FROM saved_trips 
            WHERE id=%s AND user_id=%s
        """, (trip_id, session["user_id"]))

        trip = cur.fetchone()
        con.close()

        if not trip:
            return "Trip not found", 404


        trip["description"] = "A beautiful destination saved in your bucket list."

        return render_template("my_trip_details.html", trip=trip)

    except Exception as e:
        print("MY TRIP DETAILS ERROR:", e)
        return "Error loading trip", 500


@app.route("/save-trip", methods=["POST"])
def save_trip():
    if "user_id" not in session:
        return jsonify({"status": "not_logged_in"})

    title = request.form.get("title")
    sub = request.form.get("sub")
    img = request.form.get("img")

    if not title or not sub or not img:
        print("ERROR: Missing fields =", title, sub, img)
        return jsonify({"status": "error"})

    try:
        con = get_connection()
        cur = con.cursor()

        cur.execute("""
            INSERT INTO saved_trips (user_id, title, sub, img)
            VALUES (%s, %s, %s, %s)
        """, (session["user_id"], title, sub, img))

        con.commit()
        con.close()

        return jsonify({"status": "success"})

    except Exception as e:
        print("SAVE TRIP ERROR:", e)
        return jsonify({"status": "error"})



@app.route("/remove-saved", methods=["POST"])
def remove_saved():
    if "user_id" not in session:
        return jsonify({"status": "not_logged_in"})

    trip_id = request.form.get("id")

    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute("DELETE FROM saved_trips WHERE id=%s AND user_id=%s",
                    (trip_id, session["user_id"]))
        con.commit()
        con.close()

        return jsonify({"status": "success"})
    except Exception as e:
        print("DELETE SAVED ERROR:", e)
        return jsonify({"status": "error"})
    
@app.route("/saved_details/<name>")
def destination_page(name):

    name = name.capitalize()

    destinations = [
        {"title": "Goa", "sub": "Beach & Relax", "img": url_for('static', filename='images/goa.jpg'),
         "description": "Goa is known for beaches, nightlife, seafood, and culture."},
        {"title": "Manali", "sub": "Hills & Snow", "img": url_for('static', filename='images/manali.jpg'),
         "description": "Manali is a hill station famous for snow, adventure, and scenic views."},
        {"title": "Dubai", "sub": "Luxury & Desert", "img": url_for('static', filename='images/dubai.jpg'),
         "description": "Dubai is known for luxury shopping, nightlife, and skyscrapers."},
        {"title": "Singapore", "sub": "City of Gardens", "img": url_for('static', filename='images/singapore.jpg'),
         "description": "Singapore is a clean, green, and modern travel destination."}
    ]

    for t in destinations:
        if t["title"].lower() == name.lower():
            return render_template("saved_details.html", saved_details=t)

    return "Destination not found", 404

# ============================================================
#   DESTINATIONS PAGE + TRENDING
# ============================================================


UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def get_city_info(place):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{place}"
        res = requests.get(url).json()

        return {
            "title": res.get("title"),
            "description": res.get("extract"),
            "image": res.get("thumbnail", {}).get("source")
        }
    except:
        return None



def get_destination_images(place):
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": place,
        "per_page": 6
    }
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }

    response = requests.get(url, params=params, headers=headers).json()
    
    images = []
    try:
        for photo in response["results"]:
            images.append(photo["urls"]["regular"])
    except:
        images = []

    return images


def get_weather(city):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}

    try:
        res = requests.get(url, params=params).json()

        if res.get("cod") != 200:
            return None

        return {
            "temp": res["main"]["temp"],
            "humidity": res["main"]["humidity"],
            "wind": res["wind"]["speed"],
            "condition": res["weather"][0]["main"],
            "description": res["weather"][0]["description"],
        }
    except:
        return None

def get_wiki_summary(place):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{place}"
        res = requests.get(url).json()

        if res.get("extract"):
            return res["extract"]

        return "Explore this beautiful destination for culture, attractions and travel experiences."
    except:
        return "Explore this beautiful destination for culture, attractions and travel experiences."

    
@app.route("/destination/<place>")
def destination(place):
    place_clean = place.lower()

    images = get_destination_images(place)

    weather = get_weather(place)

    description = DESTINATION_DESCRIPTIONS.get(place_clean)

    if not description:
        description = get_wiki_summary(place)

    return render_template(
        "destination.html",
        place=place.capitalize(),
        images=images,
        weather=weather,
        description=description
    )



def get_place_image(place):
    url = f"https://api.unsplash.com/search/photos?query={place}&client_id={UNSPLASH_ACCESS_KEY}&per_page=1"
    res = requests.get(url).json()
    if res.get("results"):
        return res["results"][0]["urls"]["regular"]
    return "https://picsum.photos/600/400?random=1"


@app.route("/trending")
def trending_main():
    return render_template("trending.html")


@app.route("/trending/<category>")
def trending_category(category):
    places = REAL_DESTINATIONS.get(category.lower(), [])

    data = []
    for place in places:
        data.append({
            "place": place,
            "img": get_place_image(place)
        })

    return render_template(
        "trending.html",
        destinations=data,
        category_name=category.capitalize()
    )
    
    
# ============================================================
#   FLIGHTS SEARCH
# ============================================================

GOOGLE_FLIGHTS_KEY = os.getenv("GOOGLE_FLIGHTS_KEY")
GOOGLE_FLIGHTS_HOST = "google-flights2.p.rapidapi.com"

@app.route("/search-airport")
def search_airport():
    q = request.args.get("q")
    if not q:
        return jsonify([])

    url = f"https://{GOOGLE_FLIGHTS_HOST}/api/v1/searchAirport"

    headers = {
        "x-rapidapi-key": GOOGLE_FLIGHTS_KEY,
        "x-rapidapi-host": GOOGLE_FLIGHTS_HOST
    }

    try:
        res = requests.get(url, headers=headers, params={"query": q}).json()
        print("AIRPORT RAW:", res)
    except Exception as e:
        print("AIRPORT ERROR:", e)
        return jsonify([])
    
    airports = []

    if isinstance(res.get("data"), list):
        for block in res["data"]:
            for a in block.get("list", []):
                airports.append({
                    "name": a.get("title", ""),
                    "city": a.get("city", block.get("city", "")),
                    "id": a.get("id", "")
                })
        return jsonify(airports)

    if isinstance(res, list):
        for a in res:
            airports.append({
                "name": a.get("name", ""),
                "city": a.get("city", ""),
                "id": a.get("id", "")
            })
        return jsonify(airports)

    return jsonify([])

@app.route("/flights", methods=["GET", "POST"])
def flights():
    flights_data = []
    error = None

    if request.method == "POST":

        origin_input = request.form.get("from_sky") or request.form.get("from_input")
        dest_input = request.form.get("to_sky") or request.form.get("to_input")
        date = request.form.get("date")
        return_date = request.form.get("return_date")
        trip_type = request.form.get("trip_type", "oneway")
        cabin = request.form.get("cabin", "economy").upper()
        adults = request.form.get("adults", "1")

        if not origin_input or not dest_input or not date:
            return render_template("flight_search.html", flights=[], error="All fields are required.")

        def resolve_to_iata(val):
            if not val:
                return ""
            
            v = val.strip()

            if re.match(r"^[A-Za-z]{3}$", v):
                return v.upper()

            m = re.search(r"\(([A-Za-z]{3})\)$", v)
            if m:
                return m.group(1).upper()

            try:
                url = f"https://{GOOGLE_FLIGHTS_HOST}/api/v1/searchAirport"
                res = requests.get(url, headers={
                    "x-rapidapi-key": GOOGLE_FLIGHTS_KEY,
                    "x-rapidapi-host": GOOGLE_FLIGHTS_HOST
                }, params={"query": v}).json()

                if isinstance(res.get("data"), list):
                    block = res["data"][0]
                    if block.get("list"):
                        return block["list"][0].get("id", "").upper()

                if isinstance(res, list):
                    return res[0].get("id", "").upper()

            except Exception as e:
                print("IATA RESOLVE ERROR:", e)

            return ""

        departure_id = resolve_to_iata(origin_input)
        arrival_id = resolve_to_iata(dest_input)

        if not departure_id or not arrival_id:
            return render_template("flight_search.html", flights=[], error="Could not detect the airport codes.")

        url = f"https://{GOOGLE_FLIGHTS_HOST}/api/v1/searchFlights"

        params = {
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": date,
            "travel_class": cabin,
            "adults": adults,
            "currency": "INR",
            "language_code": "en-US",
            "country_code": "IN",
            "search_type": "best"
        }

        if trip_type == "roundtrip" and return_date:
            params["return_date"] = return_date

        try:
            res = requests.get(url, headers={
                "x-rapidapi-key": GOOGLE_FLIGHTS_KEY,
                "x-rapidapi-host": GOOGLE_FLIGHTS_HOST
            }, params=params).json()

            print("GOOGLE FLIGHTS RAW:", str(res)[:2000])

        except Exception as e:
            print("FLIGHT API ERROR:", e)
            return render_template("flight_search.html", flights=[], error="No flights found for this route. Please try a different date or airport.")

        data = res.get("data", {})
        itineraries = data.get("itineraries", {})
        top_flights = itineraries.get("topFlights", [])
        alt_flights = data.get("flights", [])

        def parse_f(item):

            legs = item.get("flights", [])

            airline = None
            if legs and isinstance(legs[0], dict):
               airline = legs[0].get("airline")

            airline = airline or item.get("airline") or "Unknown Airline"

            airline_logo = item.get("airline_logo") or (legs[0].get("airline_logo") if legs else "")

            if legs:
               dep = legs[0]["departure_airport"]
               arr = legs[-1]["arrival_airport"]
               departure_airport = f"{dep['airport_name']} ({dep['airport_code']})"
               arrival_airport = f"{arr['airport_name']} ({arr['airport_code']})"
            else:
                departure_airport = arrival_airport = "N/A"

            duration = item.get("duration", {}).get("text", "N/A")


            price = item.get("price", "N/A")

            token = item.get("booking_token")
            booking_link = ""
            if token:
               booking_link = f"https://www.google.com/travel/flights?tfs={token}"

            return {
                "airline": airline,
                "airline_logo": airline_logo,
                "departureTime": departure_airport,
                "arrivalTime": arrival_airport,
                "duration": duration,
                "stops": item.get("stops", 0),
                "price": price,
                "link": booking_link,
                "legs" : legs,
            }

        flights_data = []
        for item in top_flights:
            flights_data.append(parse_f(item))

        if not flights_data:
            for f in alt_flights:
                flights_data.append(parse_f(f))

        if not flights_data:
            error = "No flights found for this route."

    return render_template("flight_search.html", flights=flights_data, error=error)


# ============================================================
#   HOTELS SEARCH
# ============================================================

BOOKING_API_KEY = os.getenv("BOOKING_API_KEY")
RAPIDAPI_HOST = "booking-com18.p.rapidapi.com"

headers_common = {
    "x-rapidapi-key": BOOKING_API_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST
}

def get_city_id(city_name):
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    params = {"query": city_name, "locale": "en-gb"}

    try:
        res = requests.get(url, headers=headers_common, params=params, timeout=8)
        data = res.json()
        print("AUTO RAW:", data)

        if data and data.get("data"):
            first = data["data"][0]

            encoded_id = first.get("id")

            if encoded_id:
                print("✔ Using encoded ID:", encoded_id)
                return encoded_id

    except Exception as e:
        print("CITY ID ERROR:", e)

    return None

def _extract_hotels_list(search_json):
    """
    Try several common response shapes to extract a list of hotels.
    """

    candidates = []
    if not isinstance(search_json, dict):
        return []

    if "result" in search_json:
        r = search_json["result"]
        if isinstance(r, dict):
        
            for key in ("hotels","search_results","results","items","data"):
                if isinstance(r.get(key), list):
                    candidates = r.get(key)
                    break
        elif isinstance(r, list):
            candidates = r

    if not candidates:
        if isinstance(search_json.get("data"), dict):
            for key in ("hotels","results","search_results","items"):
                if isinstance(search_json["data"].get(key), list):
                    candidates = search_json["data"].get(key)
                    break
        elif isinstance(search_json.get("data"), list):
            candidates = search_json.get("data")

    if not candidates and isinstance(search_json.get("hotels"), list):
        candidates = search_json.get("hotels")

    if not candidates and isinstance(search_json, list):
        candidates = search_json

    return candidates or []


def search_hotels(dest_id, checkin, checkout, adults=1):
    """
    Uses /stays/search to get hotels for a locationId.
    Returns a list of simplified hotel dicts for the template.
    """
    try:
        url = f"https://{RAPIDAPI_HOST}/stays/search"
        params = {
            "locationId": dest_id,
            "checkinDate": checkin,
            "checkoutDate": checkout,
            "adults": str(adults),
            "rooms": "1",
            "units": "metric",
            "locale": "en-gb",
            "currency": "INR",
            "page": "0",
            "rows": "25"
        }

        r = requests.get(url, headers=headers_common, params=params, timeout=20)
        data = r.json()
        print("STAYS SEARCH RAW:", data)

        hotels_raw = _extract_hotels_list(data)

        hotels = []
        for item in hotels_raw:


            hotel_id = (
                item.get("id")                     
                or item.get("hotelId")
                or item.get("hotel_id")
                )

            if not hotel_id:
                hotel_id = (item.get("property") or {}).get("id")

            if not hotel_id:
                continue

            name = (
                item.get("name")
                or (item.get("property") or {}).get("name")
                or item.get("hotel_name")
                or item.get("display_name")
            )

            address = (
                (item.get("property") or {}).get("address")
                or item.get("address")
                or item.get("location_string")
                or item.get("city")
            )

            photo_urls = item.get("photoUrls", [])
            if isinstance(photo_urls, list) and len(photo_urls) > 0:
                image = photo_urls[0]
                image = image.replace("square60", "max500")
                image = image.replace("square120", "max500")
            else:
                image = "/static/images/no-hotel.jpg"

            price_data = item.get("priceBreakdown", {})
            gross_price = price_data.get("grossPrice", {})
            price = gross_price.get("value") or 0

            try:
                price = float(price)
            except:
                pass

            rating = (
                (item.get("property") or {}).get("review_score")
                or item.get("reviewScore")
                or item.get("rating")
                or item.get("score")
            )
            
            detail_id = hotel_id
            hotels.append({
                "hotel_id": hotel_id,
                "detail_id": detail_id,         
                "name": name,
                "address": address,
                "rating": rating,
                "review_word": (item.get("property") or {}).get("review_score_word") or item.get("reviewScoreWord"),
                "image": image,
                "price": price or 0,
            })
            print(item)


        return hotels

    except Exception as e:
        print("HOTEL API ERROR:", e)
        return []



@app.route("/hotels", methods=["GET", "POST"])
def hotels():
    if request.method == "POST":
        city = request.form.get("city")
        checkin = request.form.get("checkin")
        checkout = request.form.get("checkout")

        ci = datetime.strptime(checkin, "%Y-%m-%d")
        co = datetime.strptime(checkout, "%Y-%m-%d")
        today = datetime.now()

        if ci < today:
            ci = today + timedelta(days=1)
        if co <= ci:
            co = ci + timedelta(days=2)

        checkin = ci.strftime("%Y-%m-%d")
        checkout = co.strftime("%Y-%m-%d")

    
        dest_id = get_city_id(city)
        if not dest_id:
    
            return render_template("hotel_search.html", hotels=[], city=city, checkin=checkin, checkout=checkout)

        hotels_list = search_hotels(dest_id, checkin, checkout)
        return render_template("hotel_search.html", hotels=hotels_list, city=city, checkin=checkin, checkout=checkout)

    return render_template("hotel_search.html")


@app.route("/hotel/<hotel_id>")
def hotel_details(hotel_id):
    checkin = request.args.get("checkin")
    checkout = request.args.get("checkout")
    adults = request.args.get("adults", 2)

    BASE_URL = "https://booking-com18.p.rapidapi.com"
    HEADERS = {
        "x-rapidapi-key": BOOKING_API_KEY,
        "x-rapidapi-host": "booking-com18.p.rapidapi.com"
    }

    def safe_request(url, params):
        """Wrapper to avoid app crash"""
        try:
            res = requests.get(url, headers=HEADERS, params=params, timeout=10)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.Timeout:
            print("API TIMEOUT:", url)
        except Exception as e:
            print("API ERROR:", e)
        return None

    detail_url = f"{BASE_URL}/stays/detail"
    detail_params = {
        "hotelId": hotel_id,
        "checkinDate": checkin,
        "checkoutDate": checkout,
        "adults": adults,
        "currency": "INR",
        "locale": "en-gb"
    }

    detail_data = safe_request(detail_url, detail_params)

    if not detail_data or "data" not in detail_data:
        return render_template("hotel_not_found.html")

    hotel = detail_data["data"]

    hotel_name = (
        hotel.get("name")
        or hotel.get("hotel_name")
        or "Hotel Name Not Available"
        )

    property_url = f"{BASE_URL}/stays/property-info"
    property_params = {
        "hotelId": hotel_id,
        "locale": "en-gb",
        "currency": "INR"
        }
    
    property_data = safe_request(property_url, property_params)
    description = "No description available."
    amenities = []
    
    if property_data and property_data.get("data"):
        pdata = property_data["data"]
        description = (
            pdata.get("description") or
            pdata.get("hotel_description") or
            pdata.get("summary") or
            "No description available."
            )

        if pdata.get("facilities"):
            for f in pdata["facilities"]:
                amenities.append(f.get("title") or f.get("facility_name") or f.get("name")) 

    photos = []

    if hotel.get("photos"):
        for p in hotel["photos"]:
            url = p.get("url_max300") or p.get("url_original")
            if url:
                if url.startswith("//"):
                    url = "https:" + url
                    photos.append(url)

    elif hotel.get("photoUrls"):
        photos = hotel["photoUrls"]

    elif hotel.get("mainPhotoId"):
        photos = [
            f"https://cf.bstatic.com/xdata/images/hotel/max1024x768/{hotel['mainPhotoId']}.jpg"
            ]

    if not photos or len(photos) == 0:
        photos = [
            "/static/images/hotels/hotel1.jpg",
            "/static/images/hotels/hotel2.jpg",
            "/static/images/hotels/hotel3.jpg",
            "/static/images/hotels/hotel4.jpg",
            "/static/images/hotels/hotel5.jpg",
            "/static/images/hotels/hotel6.jpg",
            "/static/images/hotels/hotel7.jpg",
            "/static/images/hotels/hotel8.jpg",
            "/static/images/hotels/hotel9.jpg",
            ]

    rooms_url = f"{BASE_URL}/stays/room-list"
    rooms_params = {
        "hotelId": hotel_id,
        "checkinDate": checkin,
        "checkoutDate": checkout,
        "adults": adults,
        "children": "0",
        "currency": "INR",
        "locale": "en-gb"
    }

    rooms_data = safe_request(rooms_url, rooms_params)

    price = None
    if rooms_data and "data" in rooms_data:
        price = rooms_data["data"].get("cheapest_avail_price_eur")


    reviews_url = f"{BASE_URL}/stays/reviews"
    reviews_params = {
        "hotel_id": hotel_id,
        "sort_by": "date_desc",
        "locale": "en-gb"
    }

    reviews_data = safe_request(reviews_url, reviews_params)
    reviews = []

    if reviews_data:
        data_block = reviews_data.get("data")
        
        if isinstance(data_block, dict):
            result_list = data_block.get("result")
            
            if isinstance(result_list, list):
                reviews = result_list[:6]  
                
    
    if not description or description == "No description available.":
        description = (
            "This property offers a comfortable stay with well-maintained rooms, "
            "friendly staff, and a peaceful environment. Conveniently located near "
            "popular attractions, it is ideal for families, couples, and solo travelers."
            )

    if not amenities or len(amenities) == 0:
        amenities = [
            "Free Wi-Fi",
            "24/7 Room Service",
            "Air Conditioning",
            "Daily Housekeeping",
            "Parking Available",
            "Restaurant & Dining Area",
            "Power Backup",
            "Comfortable Bedding",
            "Nearby Shopping & Attractions"
            ]
  
    if not reviews or len(reviews) == 0:
        reviews = [
            {"author": "Guest", "pros": "Great experience and comfortable stay!", "score": 9.0},
            {"author": "Traveler", "pros": "Clean rooms and friendly staff.", "score": 8.5},
            {"author": "Visitor", "pros": "Value for money. Good location.", "score": 8.8}
            ]

    return render_template(
       "hotel_details.html",
        hotel=hotel,
        hotel_name=hotel_name,
        photos=photos,
        amenities=amenities,
        price=price,
        reviews=reviews,
        checkin=checkin,
        checkout=checkout,
        description=description
    )

@app.template_filter("datetimeformat")
def datetimeformat(value):
    return datetime.fromtimestamp(value).strftime("%I:%M %p")


# ============================================================
#   WEATHER
# ============================================================

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

@app.route("/weather", methods=["GET", "POST"])
def weather():
    data = None
    error = None

    icon_map = {
        "Clear": "clear.svg",
        "Clouds": "clouds.svg",
        "Rain": "rain.svg",
        "Drizzle": "drizzle.svg",
        "Thunderstorm": "thunder.svg",
        "Snow": "snow.svg",

        "Mist": "mist.svg",
        "Fog": "mist.svg",
        "Haze": "haze.svg",
        "Smoke": "smoke.svg",
        "Dust": "dust.svg",
        "Sand": "sand.svg",
        "Ash": "ash.svg",

        "Tornado": "tornado.svg",
        "Squall": "squall.svg"
    }

    bg_map = {
        "Clear": "clear",
        "Clouds": "clouds",
        "Rain": "rain",
        "Drizzle": "rain",
        "Thunderstorm": "thunder",
        "Snow": "snow",
        "Mist": "mist",
        "Fog": "mist",
        "Haze": "haze",
        "Smoke": "smoke",
        "Dust": "haze",
        "Sand": "haze",
        "Ash": "haze",
        "Tornado": "thunder",
        "Squall": "thunder"
    }

    if request.method == "POST":
        city = request.form.get("city")

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}

        r = requests.get(url, params=params)
        res = r.json()

        print("WEATHER RESPONSE:", res)

        if res.get("cod") != 200:
            error = res.get("message", "City not found")
            return render_template("weather.html", data=None, error=error)

        condition = res["weather"][0]["main"]

        icon_file = icon_map.get(condition, "clear.svg")

        bg_class = bg_map.get(condition, "clear")

       
        data = {
            "temp": res["main"]["temp"],
            "feels_like": res["main"]["feels_like"],
            "humidity": res["main"]["humidity"],
            "wind": res["wind"]["speed"],
            "condition": condition,

      
            "icon": f"/static/weather-icons/{icon_file}",

            "bg": bg_class,

            "sunrise": datetime.fromtimestamp(res["sys"]["sunrise"]).strftime("%I:%M %p"),
            "sunset": datetime.fromtimestamp(res["sys"]["sunset"]).strftime("%I:%M %p")
        }

    return render_template("weather.html", data=data, error=error)


# ============================================================
#   MAP SEARCH
# ============================================================

@app.route("/map", methods=["GET", "POST"])
def map_search():
    map_url = None
    details = None
    error = None

    if request.method == "POST":
        query = request.form.get("place")

        if not query:
            error = "Please enter a location."
            return render_template("map.html", error=error)

        headers = {
            
            "User-Agent": "WanderlustAI-Map/1.0 (contact: bhaveshmulchandani651@gmail.com)"
        }

        auto_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }

        response = requests.get(auto_url, params=params, headers=headers)

        print("RAW:", response.text)

        try:
            results = response.json()
        except:
            error = "Service error. Blocked by OSM. Try after 10 minutes."
            return render_template("map.html", error=error)

        if not results:
            return render_template("map.html", error="No results found.")

        place = results[0]
        lat = place["lat"]
        lon = place["lon"]

        details = {
            "name": place.get("display_name", "Unknown"),
            "address": place.get("display_name", ""),
            "lat": lat,
            "lon": lon
        }

        map_url = (
            f"https://www.openstreetmap.org/export/embed.html?"
            f"marker={lat},{lon}&layer=mapnik&zoom=13"
        )

    return render_template("map.html", map_url=map_url, details=details, error=error)



# ============================================================
#   USER DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    stats = {
        "trips_planned": 5,
        "destinations_saved": 8,
        "flights_checked": 12,
        "favorites": 3
    }

    trending = [
        {
            "name": "Kyoto, Japan",
            "price": "12,000",
            "rating": "4.8",
            "image": "https://picsum.photos/800/600?random=21",
            "slug": "kyoto"
            },
        
        {
            
            "name": "Santorini, Greece",
            "price": "18,000",
            "rating": "4.9",
            "image": "https://picsum.photos/800/600?random=22",
            "slug": "santorini"
            
            },
        {
            
            "name": "Bali, Indonesia",
            "price": "95,000",
            "rating": "4.7",
            "image": "https://picsum.photos/800/600?random=23",
            "slug": "bali"
            },
        {
            "name": "Reykjavik, Iceland",
            "price": "14,000",
            "rating": "4.9",
            "image": "https://picsum.photos/800/600?random=24",
            "slug": "iceland"
            }
        ]

    trips = [
        {"title": "Goa", "sub": "Beach & Relax", "rating": 4.7, "img": url_for('static', filename='images/goa.jpg')},
        {"title": "Manali", "sub": "Hills & Snow", "rating": 4.6, "img": url_for('static', filename='images/manali.jpg')},
        {"title": "Dubai", "sub": "Luxury & Desert", "rating": 4.5, "img": url_for('static', filename='images/dubai.jpg')},
        {"title": "Singapore", "sub": "City of Gardens", "rating": 4.6, "img": url_for('static', filename='images/singapore.jpg')},
        ]


    profile_pic = session.get("user_avatar") or url_for('static', filename='images/default-avatar.png')

    return render_template(
        "dashboard.html",
        user_name=session.get('user_name'),
        profile_pic=profile_pic,
        stats=stats,
        trips=trips,
        trending=trending  
    )



# ============================================================
#   USER ANALYTICS TRACKING (before_request)
# ============================================================

def is_requester_admin():
    """Return True if current session is admin."""
    return "admin_id" in session

def get_location(ip):
  
    if ip == "127.0.0.1" or ip.startswith("192.168."):
        return "Mumbai", "India"

    try:
        res = requests.get(f"http://ip-api.com/json/{ip}").json()
        city = res.get("city") or "Unknown"
        country = res.get("country") or "Unknown"
        return city, country
    except:
        return "Unknown", "Unknown"

@app.before_request
def track_user():
    if "user_id" not in session:
        return

    ua = parse(request.headers.get("User-Agent"))
    ip = request.remote_addr


    if ip == "127.0.0.1":
        city = "Mumbai"
        country = "India"
    else:
     
        try:
            res = requests.get(f"http://ip-api.com/json/{ip}").json()
            city = res.get("city") or "Unknown"
            country = res.get("country") or "Unknown"
        except:
            city = "Unknown"
            country = "Unknown"

    if not city or city == "null":
        city = "Unknown"
    if not country or country == "null":
        country = "Unknown"

    device = "Mobile" if ua.is_mobile else "Desktop"
    browser = ua.browser.family or "Unknown"
    os_name = ua.os.family or "Unknown"

    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO user_analytics (user_id, ip, city, country, browser, os, device)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        session["user_id"], ip, city, country, browser, os_name, device
    ))

    con.commit()


# ============================================================
#   ADMIN AUTHENTICATION
# ============================================================

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if email.lower() != ADMIN_EMAIL.lower():
            error = "You are not authorized to access admin."
            return render_template("admin_login.html", error=error)

        con = get_connection()
        cur = con.cursor()

        cur.execute("""
            SELECT id, passwords, is_admin 
            FROM user
            WHERE email = %s
        """, (email,))
        user = cur.fetchone()

        if not user:
            error = "Admin account not found."
            return render_template("admin_login.html", error=error)

        db_hash = user["passwords"] or "" 

        print("DEBUG → form:", password)
        print("DEBUG → db_hash:", db_hash)

        if check_password_hash(db_hash, password):
            session["admin_id"] = user["id"]
            session["admin_email"] = email
            return redirect("/admin")
        else:
            error = "Incorrect password."

    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_email", None)
    flash("Logged out from admin.")
    return redirect("/admin/login")

# ============================================================
#   ADMIN DASHBOARD + ANALYTICS
# ============================================================


@app.route("/admin")
@admin_required
def admin_dashboard():
    con = get_connection()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) AS total_users FROM user")
    total_users = cur.fetchone()["total_users"]

    try:
        cur.execute("SELECT COUNT(*) AS total_flights FROM flight_searches")
        total_flights = cur.fetchone()["total_flights"]
    except:
        total_flights = 0
    try:
        cur.execute("SELECT COUNT(*) AS total_weather FROM weather_searches")
        total_weather = cur.fetchone()["total_weather"]
    except:
        total_weather = 0

    return render_template(
        "admin.html",
        total_users=total_users,
        total_flights=total_flights,
        total_weather=total_weather
    )

@app.route("/admin/api/analytics/devices")
@admin_required
def analytics_devices():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        SELECT device, COUNT(*) as total
        FROM user_analytics
        GROUP BY device
    """)
    
    rows = cur.fetchall()
    labels = [r["device"] for r in rows]
    values = [r["total"] for r in rows]

    return {"labels": labels, "values": values}


@app.route("/admin/api/analytics/browsers")
@admin_required
def analytics_browsers():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        SELECT browser, COUNT(*) as total
        FROM user_analytics
        GROUP BY browser
    """)
    
    rows = cur.fetchall()
    labels = [r["browser"] for r in rows]
    values = [r["total"] for r in rows]

    return {"labels": labels, "values": values}


@app.route("/admin/api/analytics/countries")
@admin_required
def analytics_countries():
    con = get_connection()
    cur = con.cursor()

    COUNTRY_TO_ISO = {
        "India": "IN",
        "United States": "US",
        "USA": "US",
        "Canada": "CA",
        "United Kingdom": "GB",
        "Germany": "DE",
        "France": "FR",
        "Australia": "AU",
        "Japan": "JP",
        "China": "CN",
    }

    cur.execute("""
        SELECT country, COUNT(*) AS total
        FROM user_analytics
        WHERE country IS NOT NULL AND country != ''
        GROUP BY country
        ORDER BY total DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    labels = []
    values = []

    for r in rows:
        name = r["country"]
        iso = COUNTRY_TO_ISO.get(name)

        if iso:
            labels.append(iso)
            values.append(r["total"])

    return {"labels": labels, "values": values}

@app.route("/admin/api/analytics/recent")
@admin_required
def analytics_recent():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        SELECT ua.*, u.email
        FROM user_analytics ua
        JOIN user u ON u.id = ua.user_id
        ORDER BY ua.created_at DESC
        LIMIT 20
    """)

    rows = cur.fetchall()
    return {"rows": rows}


@app.route("/admin/api/analytics/users-growth")
@admin_required
def admin_api_users_growth():
    con = get_connection()
    cur = con.cursor()

    today = datetime.now(timezone.utc).date() 

    labels = []
    data = []

    for i in range(7):
        day = today - timedelta(days=i)
        labels.append(day.strftime("%d %b"))

        cur.execute("SELECT COUNT(*) AS total FROM user WHERE DATE(created_at) = %s", (day,))
        row = cur.fetchone()
        count = row["total"] if row else 0
        data.append(count)

    labels.reverse()
    data.reverse()

    return jsonify({"labels": labels, "data": data})


@app.route("/admin/api/analytics/top-cities")
@admin_required
def admin_api_top_cities():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        SELECT destination, COUNT(*) AS cnt
        FROM flight_searches
        WHERE destination IS NOT NULL AND destination != ''
        GROUP BY destination
        ORDER BY cnt DESC
        LIMIT 6
    """)
    rows = cur.fetchall()

    if not rows:
        return {
            "labels": ["Mumbai", "Delhi", "Dubai", "London", "New York"],
            "data":   [5, 3, 2, 1, 1]
        }

    labels = [r["destination"] for r in rows]
    values = [r["cnt"] for r in rows]

    return {"labels": labels, "data": values}


@app.route("/admin/api/stats")
@admin_required
def admin_api_stats():
    con = get_connection()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) AS c FROM user")
    users = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM flight_searches")
    flights = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM weather_searches")
    weather = cur.fetchone()["c"]

    return {
        "users": users,
        "flights": flights,
        "weather": weather
    }
    
# ============================================================
#   ADMIN USER MANAGEMENT
# ============================================================

@app.route("/admin/users")
@admin_required
def admin_users():
    con = get_connection()
    cur = con.cursor()

    cur.execute("SELECT id, name, email, phone_number, is_admin, created_at FROM user ORDER BY id DESC")
    users = cur.fetchall()

    con.close()
    return render_template("admin_users.html", users=users)

@app.route("/admin/users/edit/<int:uid>", methods=["GET", "POST"])
@admin_required
def admin_edit_user(uid):
    con = get_connection()
    cur = con.cursor()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        is_admin_val = 1 if "is_admin" in request.form else 0

        cur.execute("""
            UPDATE user SET name=%s, email=%s, phone_number=%s, is_admin=%s 
            WHERE id=%s
        """, (name, email, phone, is_admin_val, uid))

        con.commit()
        admin_log(session["admin_id"], "Edited User", f"UserID={uid}")
        flash("User updated successfully!", "success")
        return redirect("/admin/users")

    cur.execute("SELECT * FROM user WHERE id=%s", (uid,))
    user = cur.fetchone()
    return render_template("admin_edit_user.html", user=user)


@app.route("/admin/users/delete/<int:uid>")
@admin_required
def admin_delete_user(uid):
    con = get_connection()
    cur = con.cursor()

    cur.execute("DELETE FROM user WHERE id=%s", (uid,))
    con.commit()

    admin_log(session["admin_id"], "Deleted User", f"UserID={uid}")

    flash("User deleted.", "danger")
    return redirect("/admin/users")


@app.route("/admin/users/make-admin/<int:uid>")
@admin_required
def admin_make_admin(uid):
    con = get_connection()
    cur = con.cursor()

    cur.execute("UPDATE user SET is_admin=1 WHERE id=%s", (uid,))
    con.commit()

    admin_log(session["admin_id"], "Promoted to Admin", f"UserID={uid}")

    flash("User promoted to admin.", "success")
    return redirect("/admin/users")


@app.route("/admin/users/remove-admin/<int:uid>")
@admin_required
def admin_remove_admin(uid):
    con = get_connection()
    cur = con.cursor()

    cur.execute("UPDATE user SET is_admin=0 WHERE id=%s", (uid,))
    con.commit()

    admin_log(session["admin_id"], "Admin Removed", f"UserID={uid}")

    flash("Admin rights removed.", "warning")
    return redirect("/admin/users")


# ----------------------------
#   ADMIN LOGS
# ----------------------------

def admin_log(admin_id, action, meta=""):
    try:
        con = get_connection()
        cur = con.cursor()
        cur.execute("INSERT INTO admin_logs (admin_id, action, meta) VALUES (%s, %s, %s)", (admin_id, action, meta))
        con.commit()
    except Exception as e:
        print("Admin log failed:", e)


@app.route("/admin/logs")
@admin_required
def admin_logs():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""  
        SELECT 
            l.id,
            u.name AS admin_name,
            l.action,
            l.meta,
            l.created_at
        FROM admin_logs l
        LEFT JOIN user u ON l.admin_id = u.id
        ORDER BY l.created_at DESC
        LIMIT 200
    """)

    logs = cur.fetchall()
    return render_template("admin_logs.html", logs=logs)

# ============================================================
#   ADMIN SETTINGS
# ============================================================

@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    con = get_connection()
    cur = con.cursor()

    admin_id = session["admin_id"]
    
    if request.method == "POST":
        new_email = request.form["email"]
        new_pass = request.form["password"]
        
        if new_pass.strip() == "":
           cur.execute("UPDATE user SET email=%s WHERE id=%s", (new_email, admin_id))
        else:
            hashed = generate_password_hash(new_pass)
            cur.execute("UPDATE user SET email=%s, passwords=%s WHERE id=%s",
                       (new_email, hashed, admin_id))
           
            con.commit()
            session["admin_email"] = new_email
           
            admin_log(admin_id, "Updated Admin Settings")
           
            flash("Settings updated successfully!", "success")
            return redirect("/admin/settings")


    cur.execute("SELECT * FROM user WHERE id=%s", (admin_id,))
    admin = cur.fetchone()

    con.close()
    return render_template("admin_settings.html", admin=admin)

# ============================================================
#   AI ASSISTANT (EURI)
# ============================================================

EURON_API_KEY = os.getenv("EURON_API_KEY")
print("EURON_API_KEY loaded:", bool(EURON_API_KEY))

@app.route("/api/start_chat", methods=["POST"])
def start_chat():
    con = get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO conversations (title) VALUES ('New Chat')")
    con.commit()
    chat_id = cur.lastrowid            
    cur.execute("""
                INSERT INTO messages (conversation_id, sender, text) 
                VALUES (%s, 'bot', %s)
                """, (chat_id, "Hello! I'm Euri, your travel assistant. How can I help you today?"))
    con.commit()

    cur.close()
    con.close()

    return jsonify({"conversation_id": chat_id})

@app.route("/api/new_chat", methods=["POST"])
def new_chat():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO conversations (title)
        VALUES ('New Chat')
    """)
    con.commit()

    chat_id = cur.lastrowid

    cur.execute("""
        INSERT INTO messages (conversation_id, sender, text)
        VALUES (%s, 'bot', %s)
        """, (chat_id, "Hello! I'm Euri, your travel assistant. How can I help you today?"))
    con.commit()
    cur.close()
    con.close()

    return jsonify({"conversation_id": chat_id})

@app.route("/api/chats")
def get_chats():
    con = get_connection()
    cur = con.cursor()

    cur.execute("SELECT id, title FROM conversations ORDER BY id DESC")
    chats = cur.fetchall()

    cur.close()
    con.close()
    return jsonify(chats)

@app.route("/api/chat/<int:chat_id>")
def get_chat(chat_id):
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        SELECT sender, text FROM messages
        WHERE conversation_id = %s
        ORDER BY id ASC
    """, (chat_id,))
    msgs = cur.fetchall()

    cur.close()
    con.close()
    return jsonify(msgs)

@app.route("/api/assistant", methods=["POST"])
def ai_assistant():
    data = request.json
    user_msg = data.get("message")
    chat_id = data.get("conversation_id")

    if not chat_id:
        return jsonify({"reply": "Error: No conversation id!"})

    con = get_connection()
    cur = con.cursor()
    
    cur.execute("""
        INSERT INTO messages (conversation_id, sender, text)
        VALUES (%s, 'user', %s)
        """, (chat_id, user_msg))
    con.commit()

    cur.execute("""
            UPDATE conversations
            SET title = %s
            WHERE id = %s AND (title = 'New Chat' OR title IS NULL)
            """, (user_msg[:40], chat_id))
    con.commit()

    payload = {
        "model": "gpt-4.1-nano",
        "messages": [
            {"role": "system", "content": "You are Euri, a smart AI travel assistant."},
            {"role": "user", "content": user_msg}
        ]
    }

    headers = {
        "Authorization": f"Bearer {EURON_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(
        "https://api.euron.one/api/v1/euri/chat/completions",
        json=payload,
        headers=headers
    ).json()
    
    if "choices" not in r:
        print("EURI API ERROR RESPONSE:", r)
        reply = "Sorry, Euri is currently unavailable. Please try again."
    else:
        reply = r["choices"][0]["message"]["content"]

    cur.execute("""
        INSERT INTO messages (conversation_id, sender, text)
        VALUES (%s, 'bot', %s)
    """, (chat_id, reply))
    con.commit()

    cur.close()
    con.close()

    return jsonify({"reply": reply})


@app.route("/api/chat/<int:chat_id>/delete", methods=["DELETE"])
def delete_chat(chat_id):
    db = get_connection()
    cursor = db.cursor()

    cursor.execute("DELETE FROM messages WHERE conversation_id = %s", (chat_id,))
    cursor.execute("DELETE FROM conversations WHERE id = %s", (chat_id,))
    db.commit()

    return jsonify({"status": "deleted"})


@app.route("/api/chat/<int:chat_id>/rename", methods=["POST"])
def rename_chat(chat_id):
    new_title = request.json.get("title")

    db = get_connection()
    cursor = db.cursor()

    cursor.execute("UPDATE conversations SET title = %s WHERE id = %s", (new_title, chat_id))
    db.commit()

    return jsonify({"status": "renamed"})

@app.route("/travel-ai")
def travel_ai():
    return render_template("travel_ai.html")


# ============================================================
#   RUN APP
# ============================================================

if __name__ == "__main__":
    app.run(port=5000, debug=False)
