import sqlite3
from flask import Flask, render_template

app = Flask(__name__)
DB_NAME = "hotel.db"


def init_db():
  """Initializes the SQLite database with the required tables and mock data."""
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  # Create tables
  cursor.execute(
      "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY,"
      " username TEXT, role TEXT)"
  )
  cursor.execute(
      "CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY, room_number"
      " TEXT, status TEXT)"
  )
  cursor.execute(
      "CREATE TABLE IF NOT EXISTS security_logs (id INTEGER PRIMARY KEY,"
      " timestamp TEXT, username TEXT, event TEXT)"
  )
  cursor.execute(
      "CREATE TABLE IF NOT EXISTS equipment (id INTEGER PRIMARY KEY,"
      " equipment_name TEXT, temperature REAL, vibration REAL, operating_hours"
      " INTEGER)"
  )
  cursor.execute(
      "CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY,"
      " incident_name TEXT, impact INTEGER, probability INTEGER, urgency"
      " INTEGER)"
  )

  # Seed mock data if tables are empty
  cursor.execute("SELECT COUNT(*) FROM security_logs")
  if cursor.fetchone()[0] == 0:
    security_logs = [
        ("09:31", "reception01", "Login success"),
        ("09:32", "reception01", "Login failed"),
        ("09:32", "reception01", "Login failed"),
        ("09:33", "reception01", "Login failed"),
        ("09:33", "reception01", "Login failed"),
    ]
    cursor.executemany(
        "INSERT INTO security_logs (timestamp, username, event) VALUES (?, ?,"
        " ?)",
        security_logs,
    )

  cursor.execute("SELECT COUNT(*) FROM equipment")
  if cursor.fetchone()[0] == 0:
    equipments = [
        ("HVAC-01", 65.0, 2.1, 4000),
        ("HVAC-02", 81.0, 7.8, 8200),
        ("PUMP-01", 54.0, 1.8, 3000),
        ("BOILER-01", 84.0, 8.1, 9100),
    ]
    cursor.executemany(
        "INSERT INTO equipment (equipment_name, temperature, vibration,"
        " operating_hours) VALUES (?, ?, ?, ?)",
        equipments,
    )

  cursor.execute("SELECT COUNT(*) FROM incidents")
  if cursor.fetchone()[0] == 0:
    incidents = [
        ("Suspicious login", 9, 8, 9),  # Priority = 9 * 8 * 9 = 648 / normalized
        ("HVAC failure", 8, 7, 8),
        ("Wi-Fi outage", 7, 6, 8),
        ("Low occupancy", 5, 4, 6),
        ("Slow check-in", 6, 5, 5),
    ]
    cursor.executemany(
        "INSERT INTO incidents (incident_name, impact, probability, urgency)"
        " VALUES (?, ?, ?, ?)",
        incidents,
    )

  conn.commit()
  conn.close()


@app.route("/")
def dashboard():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  # Fetch Equipment & Evaluate Risk Rules
  cursor.execute(
      "SELECT equipment_name, temperature, vibration, operating_hours FROM"
      " equipment"
  )
  equip_rows = cursor.fetchall()
  equipment_eval = []
  high_risk_equip_count = 0

  for name, temp, vib, hours in equip_rows:
    # Rule-based risk assessment
    if temp > 75 or vib > 5.0 or hours > 8000:
      risk = "HIGH"
      high_risk_equip_count += 1
    else:
      risk = "LOW"
    equipment_eval.append({"name": name, "risk": risk})

  # Fetch Security Stats
  cursor.execute("SELECT COUNT(*) FROM security_logs WHERE event LIKE '%fail%'")
  failed_logins = cursor.fetchone()[0]

  # Fetch & Calculate Incident Priorities (Priority = Impact * Probability * Urgency)
  cursor.execute(
      "SELECT incident_name, impact, probability, urgency FROM incidents"
  )
  incidents_raw = cursor.fetchall()
  prioritized_actions = []

  for name, imp, prob, urg in incidents_raw:
    score = imp * prob * urg
    prioritized_actions.append({"name": name, "score": score})

  # Sort by priority score descending
  prioritized_actions = sorted(
      prioritized_actions, key=lambda x: x["score"], reverse=True
  )

  conn.close()

  # Dashboard Context Data
  context = {
      "occupancy": "78%",
      "cyber_risk": "MEDIUM",
      "operational_risk": "LOW",
      "equipment_risk": (
          "HIGH" if high_risk_equip_count > 0 else "LOW"
      ),
      "failed_logins": failed_logins,
      "suspicious_events": 6,
      "critical_alerts": 2,
      "high_risk_equipment": high_risk_equip_count,
      "upcoming_maintenance": 8,
      "predicted_failures": high_risk_equip_count,
      "top_actions": [item["name"] for item in prioritized_actions[:3]],
  }

  return render_template("dashboard.html", **context)


if __name__ == "__main__":
  init_db()
  app.run(debug=True, port=5000)
