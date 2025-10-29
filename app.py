from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash
import sqlite3
from sqlite3 import Connection
import csv
import io
import os
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "data", "reservas.db")

def get_db() -> Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    create_sql = (
        "CREATE TABLE IF NOT EXISTS reservas ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "nombre TEXT NOT NULL,"
        "correo TEXT,"
        "telefono TEXT,"
        "fecha_llegada TEXT,"
        "fecha_salida TEXT,"
        "habitaciones INTEGER,"
        "total REAL,"
        "created_at TEXT DEFAULT (datetime('now'))"
        ")"
    )
    cur.execute(create_sql)
    conn.commit()
    conn.close()

def seed_sample():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) as c FROM reservas")
    if cur.fetchone()["c"] == 0:
        sample = [
            ("María López","maria@example.com","3001112222","2025-11-10","2025-11-13",1,240.0),
            ("Carlos Pérez","carlos@example.com","3003334444","2025-12-01","2025-12-05",2,600.0),
            ("Ana Gómez","ana@example.com","3005556666","2026-01-08","2026-01-10",1,160.0),
        ]
        cur.executemany("INSERT INTO reservas (nombre, correo, telefono, fecha_llegada, fecha_salida, habitaciones, total) VALUES (?,?,?,?,?,?,?)", sample)
        conn.commit()
    conn.close()

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-this"

@app.before_request
def setup():
    init_db()
    seed_sample()
    upload_csv = os.path.join(BASE_DIR, "data", "import_reservas.csv")
    if os.path.exists(upload_csv):
        try:
            conn = get_db()
            cur = conn.cursor()
            with open(upload_csv, newline='', encoding='utf-8') as fh:
                reader = csv.DictReader(fh)
                rows = []
                for r in reader:
                    rows.append((
                        r.get("nombre") or r.get("Nombre") or "",
                        r.get("correo") or r.get("Correo") or "",
                        r.get("telefono") or r.get("Telefono") or "",
                        r.get("fecha_llegada") or r.get("FechaLlegada") or "",
                        r.get("fecha_salida") or r.get("FechaSalida") or "",
                        int(r.get("habitaciones") or r.get("Habitaciones") or 1),
                        float(r.get("total") or r.get("Total") or 0.0)
                    ))
                cur.executemany("INSERT INTO reservas (nombre, correo, telefono, fecha_llegada, fecha_salida, habitaciones, total) VALUES (?,?,?,?,?,?,?)", rows)
                conn.commit()
        except Exception as e:
            print("Import CSV failed:", e)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reservas")
def reservas():
    page = max(1, int(request.args.get("page", 1)))
    per_page = int(request.args.get("per_page", 10))
    offset = (page-1)*per_page

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) as total FROM reservas")
    total = cur.fetchone()["total"]

    cur.execute("SELECT * FROM reservas ORDER BY created_at DESC LIMIT ? OFFSET ?", (per_page, offset))
    rows = cur.fetchall()
    reservas = [dict(r) for r in rows]
    conn.close()

    total_pages = (total + per_page - 1) // per_page
    return render_template("reservas.html", reservas=reservas, page=page, per_page=per_page, total=total, total_pages=total_pages)

@app.route("/reservas/new", methods=["GET","POST"])
def reservas_new():
    if request.method == "POST":
        nombre = request.form.get("nombre","").strip()
        correo = request.form.get("correo","").strip()
        telefono = request.form.get("telefono","").strip()
        fecha_llegada = request.form.get("fecha_llegada","")
        fecha_salida = request.form.get("fecha_salida","")
        habitaciones = int(request.form.get("habitaciones","1") or 1)
        total = float(request.form.get("total","0") or 0.0)

        if not nombre:
            flash("El nombre es requerido", "danger")
            return redirect(url_for("reservas_new"))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO reservas (nombre, correo, telefono, fecha_llegada, fecha_salida, habitaciones, total) VALUES (?,?,?,?,?,?,?)", (nombre, correo, telefono, fecha_llegada, fecha_salida, habitaciones, total))
        conn.commit()
        conn.close()
        flash("Reserva creada correctamente", "success")
        return redirect(url_for("reservas"))

    return render_template("reservas_new.html")

@app.route("/reservas/export")
def reservas_export():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reservas ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id","nombre","correo","telefono","fecha_llegada","fecha_salida","habitaciones","total","created_at"])
    for r in rows:
        writer.writerow([r["id"], r["nombre"], r["correo"], r["telefono"], r["fecha_llegada"], r["fecha_salida"], r["habitaciones"], r["total"], r["created_at"]])

    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)
    filename = f"reservas_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(mem, as_attachment=True, download_name=filename, mimetype="text/csv")

@app.route("/api/reservas")
def api_reservas():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reservas ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(debug=True)

