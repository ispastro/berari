# ✈️ Avaitor — Ethiopian Airlines Pilot Trainee Vacancy Monitor

**Avaitor** is an automated 24/7 background monitor and interactive Telegram bot designed to detect Ethiopian Airlines pilot trainee openings the instant they are announced.

---

## 🌟 Key Features

1. **Multi-Source Redundancy (Zero Missed Postings):**
   - **Corporate Careers:** `corporate.ethiopianairlines.com/AboutEthiopian/careers/vacancies`
   - **Ethiopian Aviation University (EAU):** `eau.edu.et` & `/programs` (Cadet, Ab-Initio & CPL Programs)
   - **Ethiojobs Official Syndication:** `ethiojobs.net/jobs-in-ethiopia/ethiopian-airlines-group/`

2. **Smart Precision Filtering:**
   - Targets: `Pilot Trainee`, `Trainee Pilot`, `Cadet Pilot`, `Student Pilot`, `Commercial Pilot License`, `Ab-Initio`.
   - Automatically filters out non-pilot airline jobs (Cabin crew, technicians, ticketing, IT, cargo).
   - Automatically extracts eligibility info (Age, Education/Degree, Minimum Height, Application Deadline).

3. **Instant Mobile Alerts via Telegram:**
   - Push notifications to your smartphone the moment a vacancy appears.
   - Clean HTML cards with rich details and an inline **[✈️ Open Application Page]** button.

4. **Remote Interactive Controls in Telegram:**
   - `/check` — Triggers an on-demand live scrape across all portals right now.
   - `/status` — Displays system health, uptime, last check timestamp, and active vacancy counts.
   - `/latest` — Displays the most recent pilot announcements logged.
   - `/test` — Sends a test alert card to your phone to verify sound and formatting.
   - `/stop` — Temporarily mutes alerts.

5. **Persistent & Scalable Storage:**
   - Embedded SQLite with Write-Ahead Logging (WAL) for high concurrency and zero memory overhead.
   - Cryptographic fingerprinting to prevent duplicate alerts.

---

## 🚀 Quick Setup (Under 2 Minutes)

### Step 1: Create Your Free Telegram Bot
1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot`, choose a name and username (e.g. `MyAvaitorBot`).
3. Copy the **HTTP API Token** provided by BotFather.
4. Get your Telegram Chat ID:
   - Search for **[@userinfobot](https://t.me/userinfobot)** on Telegram and press `/start`, or simply run `/start` with your newly created bot.

### Step 2: Configure `.env`
Create a `.env` file from the provided template:

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```ini
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=123456789
CHECK_INTERVAL_MINUTES=15
```

---

## 🎮 How to Run

### Option A: Quick Command-Line Tests

* **Run a live scan right now:**
  ```bash
  ./run.sh --check-once
  ```

* **Check database and monitor status:**
  ```bash
  ./run.sh --status
  ```

* **Send a test alert to your Telegram:**
  ```bash
  ./run.sh --test-alert
  ```

### Option B: Run 24/7 in Background

Simply start the monitor daemon:

```bash
./run.sh
```

### Option C: Run as a Linux Systemd Service (Auto-start on boot)

```bash
# 1. Copy service file to systemd
sudo cp avaitor.service /etc/systemd/system/

# 2. Reload and enable service
sudo systemctl daemon-reload
sudo systemctl enable --now avaitor.service

# 3. Check logs
sudo journalctl -u avaitor.service -f
```

---

## 🧪 Unit Tests

Run the built-in test suite to verify matching and database operations:

```bash
.venv/bin/python tests/test_monitor.py
```
