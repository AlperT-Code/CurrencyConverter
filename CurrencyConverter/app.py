from flask import Flask, render_template, request
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

API_KEY = "d78a3069992d3b8a9ff268f5"
BASE_URL = "https://v6.exchangerate-api.com/v6"

                                                                                                                                                       
def init_db():
    conn = sqlite3.connect("exchange.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            base TEXT,
            target TEXT,
            rate REAL,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    base_currency = ""
    target_currency = ""
    amount = ""

    if request.method == "POST":
        base_currency = request.form["base"].upper()
        target_currency = request.form["target"].upper()
        amount = float(request.form["amount"])

        url = f"{BASE_URL}/{API_KEY}/latest/{base_currency}"
        r = requests.get(url)
        data = r.json()

        if r.status_code != 200 or data.get("result") != "success":
            error = data.get("error-type", "API hatası.")
        else:
            rate = data["conversion_rates"].get(target_currency)
            if rate:
                converted = round(amount * rate, 2)
                result = {
                    "text": f"{amount} {base_currency} = {converted} {target_currency}",
                    "base": base_currency,
                    "target": target_currency
                }


                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = sqlite3.connect("exchange.db")
                c = conn.cursor()
                c.execute("INSERT INTO rates (base, target, rate, date) VALUES (?, ?, ?, ?)",
                          (base_currency, target_currency, rate, now))
                conn.commit()
                conn.close()
            else:
                error = f"{target_currency} için kur bilgisi bulunamadı."

    return render_template("index.html",
                           result=result,
                           error=error,
                           base=base_currency,
                           target=target_currency,
                           amount=amount)


@app.route("/grafik/<base>/<target>")
def grafik(base, target):
    conn = sqlite3.connect("exchange.db")
    c = conn.cursor()
    c.execute("""
        SELECT date, rate FROM rates
        WHERE base=? AND target=?
        ORDER BY date DESC LIMIT 10
    """, (base, target))
    data = c.fetchall()
    conn.close()

    dates = [d[0] for d in data][::-1]
    rates = [d[1] for d in data][::-1]

    return render_template("grafik.html", base=base, target=target, dates=dates, rates=rates)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
