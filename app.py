from flask import Flask, render_template, request, redirect, session
import sqlite3
from event_config import EVENT

app = Flask(__name__)
app.secret_key = "sienna2027-lulipanpin-secreto"

ADMIN_PASSWORD = "sienna2027"


def init_db():
    conn = sqlite3.connect("guests.db")
    cursor = conn.cursor()

    # Crear tabla si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            companions INTEGER NOT NULL DEFAULT 0,
            confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migración: agregar confirmed_at si no existe (base de datos vieja)
    cursor.execute("PRAGMA table_info(guests)")
    columns = [row[1] for row in cursor.fetchall()]
    if "confirmed_at" not in columns:
        cursor.execute("ALTER TABLE guests ADD COLUMN confirmed_at TIMESTAMP")

    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        companions = request.form.get("companions", 0)
        if name:
            conn = sqlite3.connect("guests.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO guests (name, companions) VALUES (?, ?)",
                (name, companions)
            )
            conn.commit()
            conn.close()
        return redirect("/?confirmed=1")

    confirmed = request.args.get("confirmed")
    return render_template("index.html", event=EVENT, confirmed=confirmed)


@app.route("/admin", methods=["GET"])
def admin():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect("guests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, companions, confirmed_at FROM guests ORDER BY confirmed_at DESC")
    guests = cursor.fetchall()
    total_personas = sum((g[2] or 0) + 1 for g in guests)
    conn.close()

    return render_template("admin.html", guests=guests, total=total_personas, event=EVENT)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/admin")
        else:
            error = "Contraseña incorrecta"
    return render_template("admin_login.html", error=error, event=EVENT)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin/login")


@app.route("/admin/delete/<int:guest_id>", methods=["POST"])
def delete_guest(guest_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")
    conn = sqlite3.connect("guests.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guests WHERE id = ?", (guest_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")
init_db()

if __name__ == "__main__":
    app.run(debug=True)