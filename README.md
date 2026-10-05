# 🇪🇹 Berari (በራሪ) — Ethiopian Airlines Career Monitor (`@EtwingBot`)

**Berari (በራሪ)** is an automated 24/7 background monitor and interactive Telegram bot ([@EtwingBot](https://t.me/EtwingBot)) designed to detect Ethiopian Airlines career openings the instant they are announced.

---

## 🌟 Multi-Role Career Tracks

Users can choose their preferred alert track with one tap:

1. ✈️ **Pilot & Cadet Track:**
   * Pilot Trainee (ET-Sponsored & Self-Sponsored)
   * Cadet Pilot Programs
   * Ab-Initio & Commercial Pilot License (CPL)
   * First Officer Trainee

2. 🧑‍✈️ **Cabin Crew Track:**
   * Trainee Cabin Crew
   * Flight Attendant Announcements
   * Air Hostess Programs

3. 🔧 **Aircraft Maintenance & Tech Track:**
   * Aircraft Maintenance Technician (AMT)
   * Aircraft Mechanic Trainee
   * Avionics & Maintenance Engineering Programs

4. 🌐 **All Vacancies Track:**
   * Receive instant alerts for all aviation opportunities across Ethiopian Airlines and Ethiopian Aviation University.

---

## 📡 Monitored Portals

1. **Official Corporate Vacancies Portal:**  
   `https://corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies`
2. **Ethiopian Aviation University (EAU):**  
   `https://eau.edu.et` & `/programs`
3. **Official Ethiojobs Syndication:**  
   `https://www.ethiojobs.net/jobs-in-ethiopia/ethiopian-airlines-group/`

---

## 💬 Interactive Telegram Commands (`@EtwingBot`)

* `/start` — Subscribe to alerts and pick your career track (Pilot, Cabin Crew, Maintenance, or All).
* `/track` — Change your preferred alert category anytime with inline buttons.
* `/check` — Run an immediate live scan across all Ethiopian portals on demand.
* `/status` — View bot uptime, active vacancy counts by role, and last check timestamp.
* `/latest` — View the most recent vacancies logged for your chosen track.
* `/test` — Send a sample alert card to your phone to test notifications and sound.
* `/stop` — Unsubscribe from alerts.

---

## 🚀 Quick Setup & Running

Your bot token is configured in `.env`.

### 1. Run a Live Scan (CLI Test)
```bash
./run.sh --check-once
```

### 2. View Database Status
```bash
./run.sh --status
```

### 3. Start the 24/7 Daemon & Telegram Bot
```bash
./run.sh
```

Once running, open Telegram, find **[@EtwingBot](https://t.me/EtwingBot)**, and send `/start`!

### 4. Run as a Background Linux Systemd Service
```bash
sudo cp avaitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now avaitor.service
```

---

## 🧪 Unit Tests

Run the comprehensive unit test suite:
```bash
.venv/bin/python tests/test_monitor.py
```
