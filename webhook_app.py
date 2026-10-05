import os
import sys
import logging
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config import BOT_NAME, BOT_USERNAME, TELEGRAM_BOT_TOKEN
from bot import AvaitorApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BerariWebhook")

app = Flask(__name__)
avaitor_app = AvaitorApp()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Berari (በራሪ) — Ethiopian Airlines Career Monitor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .card { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }
        .stat-val { font-size: 2.2rem; font-weight: 700; }
        .badge-pilot { background-color: #1f6feb; color: white; }
        .badge-cabin { background-color: #a371f7; color: white; }
        .badge-tech { background-color: #238636; color: white; }
        .btn-tg { background-color: #2da44e; color: white; font-weight: 600; }
        .btn-tg:hover { background-color: #2c974b; color: white; }
        .table-dark { --bs-table-bg: #161b22; --bs-table-border-color: #30363d; }
    </style>
</head>
<body class="py-4">
    <div class="container" style="max-width: 960px;">
        <!-- Header -->
        <div class="card p-4 mb-4 text-center">
            <h1 class="h2 text-white mb-2">🇪🇹 Berari (በራሪ)</h1>
            <p class="text-secondary mb-3">Automated 24/7 Ethiopian Airlines Career Monitor & Telegram Bot</p>
            <div>
                <a href="https://t.me/{{ bot_username }}" target="_blank" class="btn btn-tg px-4 py-2">
                    ✈️ Open @{{ bot_username }} on Telegram
                </a>
                <a href="/check" class="btn btn-outline-secondary px-3 py-2 ms-2">🔄 Trigger Scan</a>
            </div>
        </div>

        <!-- Metrics Grid -->
        <div class="row g-3 mb-4">
            <div class="col-6 col-md-3">
                <div class="card p-3 text-center">
                    <div class="text-secondary small">Total Vacancies</div>
                    <div class="stat-val text-white">{{ stats.total_vacancies }}</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="card p-3 text-center">
                    <div class="text-secondary small">✈️ Pilot Trainee</div>
                    <div class="stat-val text-primary">{{ stats.pilot_vacancies }}</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="card p-3 text-center">
                    <div class="text-secondary small">🧑‍✈️ Cabin Crew</div>
                    <div class="stat-val" style="color: #a371f7;">{{ stats.cabin_vacancies }}</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="card p-3 text-center">
                    <div class="text-secondary small">🔧 Maintenance</div>
                    <div class="stat-val text-success">{{ stats.maintenance_vacancies }}</div>
                </div>
            </div>
        </div>

        <!-- Status Details -->
        <div class="card p-3 mb-4">
            <div class="row text-secondary small">
                <div class="col-md-4">👥 Active Subscribers: <strong class="text-white">{{ stats.subscribers_count }}</strong></div>
                <div class="col-md-4">⏱️ Last Scrape: <strong class="text-white">{{ stats.last_scrape_time }}</strong></div>
                <div class="col-md-4">🚦 Last Status: <strong class="text-success">{{ stats.last_scrape_status }}</strong></div>
            </div>
        </div>

        <!-- Recent Vacancies Table -->
        <div class="card p-4">
            <h5 class="text-white mb-3">📋 Recently Tracked Vacancies</h5>
            {% if vacancies %}
            <div class="table-responsive">
                <table class="table table-dark table-hover align-middle mb-0">
                    <thead>
                        <tr class="text-secondary small">
                            <th>Track</th>
                            <th>Job Title</th>
                            <th>Source</th>
                            <th>Deadline</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for vac in vacancies %}
                        <tr>
                            <td>
                                {% if vac.category == 'PILOT' %}
                                    <span class="badge badge-pilot">Pilot</span>
                                {% elif vac.category == 'CABIN_CREW' %}
                                    <span class="badge badge-cabin">Cabin Crew</span>
                                {% else %}
                                    <span class="badge badge-tech">Maintenance</span>
                                {% endif %}
                            </td>
                            <td class="fw-semibold text-white">{{ vac.title }}</td>
                            <td class="text-secondary small">{{ vac.source }}</td>
                            <td class="text-secondary small">{{ vac.deadline or 'See portal' }}</td>
                            <td>
                                <a href="{{ vac.url }}" target="_blank" class="btn btn-sm btn-outline-primary">Apply ↗</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <p class="text-secondary mb-0">No vacancies recorded yet. Tap "Trigger Scan" above to run the initial check.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    """Render public status dashboard."""
    stats = avaitor_app.db.get_stats()
    vacancies = avaitor_app.db.get_recent_vacancies(limit=15)
    return render_template_string(
        DASHBOARD_HTML,
        stats=stats,
        vacancies=vacancies,
        bot_username=BOT_USERNAME,
        bot_name=BOT_NAME,
    )

@app.route("/check", methods=["GET", "POST"])
def check():
    """Trigger on-demand check cycle (callable via cron or browser)."""
    try:
        new_items = avaitor_app.run_check_cycle()
        return jsonify({
            "status": "success",
            "new_vacancies_found": len(new_items),
            "items": new_items,
        })
    except Exception as e:
        logger.error(f"Error in /check endpoint: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive Telegram webhook events."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return "No payload", 400

    # Handle /start or button callbacks from Telegram
    if "callback_query" in data:
        cb = data["callback_query"]
        cb_id = cb["id"]
        chat_id = str(cb["message"]["chat"]["id"])
        cb_data = cb.get("data", "")
        
        if cb_data.startswith("set_track:"):
            chosen_track = cb_data.split(":", 1)[1]
            avaitor_app.db.set_subscriber_track(chat_id, chosen_track)
            
            # Answer callback
            avaitor_app.notifier.send_message(
                chat_id=chat_id,
                text=f"✅ <b>Preferences Updated!</b>\n\nYou will now receive alerts for: <b>{chosen_track}</b>."
            )

    elif "message" in data:
        msg = data["message"]
        chat_id = str(msg["chat"]["id"])
        text = msg.get("text", "").strip()
        user = msg.get("from", {})

        if text.startswith("/start"):
            avaitor_app.db.add_subscriber(
                chat_id=chat_id,
                username=user.get("username"),
                first_name=user.get("first_name"),
                track="ALL"
            )
            # Send welcome message
            from tg_bot.handlers import get_track_keyboard, TRACK_NAMES
            markup = get_track_keyboard().to_dict()
            avaitor_app.notifier.send_message(
                chat_id=chat_id,
                text=(
                    f"👋 Selam <b>{user.get('first_name', 'there')}</b>!\n\n"
                    "🇪🇹 Welcome to <b>Berari (በራሪ) — Ethiopian Airlines Career Monitor</b>!\n\n"
                    "🔔 You are subscribed to instant alerts for Ethiopian Airlines & Aviation University.\n\n"
                    "👇 <b>Select the career track you want to receive alerts for:</b>"
                ),
                reply_markup=markup
            )

        elif text.startswith("/status"):
            stats = avaitor_app.db.get_stats()
            user_track = avaitor_app.db.get_subscriber_track(chat_id)
            avaitor_app.notifier.send_message(
                chat_id=chat_id,
                text=(
                    "📊 <b>Berari (በራሪ) Monitor Status</b>\n\n"
                    f"🟢 <b>Status:</b> Active 24/7 on PythonAnywhere\n"
                    f"🎯 <b>Your Track:</b> {user_track}\n"
                    f"👥 <b>Subscribers:</b> {stats['subscribers_count']}\n"
                    f"✈️ Pilot Vacancies: {stats.get('pilot_vacancies', 0)}\n"
                    f"🧑‍✈️ Cabin Crew: {stats.get('cabin_vacancies', 0)}\n"
                    f"🔧 Maintenance: {stats.get('maintenance_vacancies', 0)}\n"
                    f"⏱️ Last Scan: <code>{stats['last_scrape_time']}</code>"
                )
            )

        elif text.startswith("/check"):
            avaitor_app.notifier.send_message(chat_id, "🔄 Running live scan across Ethiopian portals...")
            items = avaitor_app.run_check_cycle()
            avaitor_app.notifier.send_message(
                chat_id,
                f"✅ Scan finished! Discovered {len(items)} new opening(s)." if items else "✅ Scan finished. No newly posted vacancies since last check."
            )

        elif text.startswith("/test"):
            user_track = avaitor_app.db.get_subscriber_track(chat_id)
            avaitor_app.notifier.send_test_alert(chat_id, category=user_track if user_track != "ALL" else "PILOT")

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
