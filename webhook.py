from flask import Flask, request
import sqlite3

app = Flask(__name__)

DB = "saas.db"


def connect():
    return sqlite3.connect(DB)


def upgrade_user(email):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET plan = 'pro'
        WHERE email = ?
    """, (email,))

    conn.commit()
    conn.close()


@app.route("/flutterwave-webhook", methods=["POST"])
def flutterwave_webhook():
    data = request.json

    try:
        status = data["data"]["status"]
        email = data["data"]["customer"]["email"]

        # Only upgrade if payment successful
        if status == "successful":
            upgrade_user(email)

        return {"status": "ok"}

    except Exception as e:
        return {"error": str(e)}