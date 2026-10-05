# 🚀 Deploying Berari (@EtwingBot) to PythonAnywhere

This guide provides step-by-step instructions for deploying your Ethiopian Airlines Career Monitor to **PythonAnywhere**.

---

## 📋 Prerequisites
* A [PythonAnywhere account](https://www.pythonanywhere.com/) (Free or Paid).
* Your Telegram Bot Token (`8737970445:AAF_AQwMPTlb7Z880YN8Q3UHl5RnSs40H3M`).

---

## 🛠️ Step 1: Clone the Code to PythonAnywhere

1. Log into your [PythonAnywhere Dashboard](https://www.pythonanywhere.com/).
2. Go to the **Consoles** tab and click **Bash** to open a new terminal.
3. Clone your project or upload the directory:
   ```bash
   git clone <YOUR_GIT_REPO_URL> Avaitor
   cd Avaitor
   ```
   *(Or if uploading via zip, unzip into `/home/<yourusername>/Avaitor`)*.

---

## 📦 Step 2: Set Up Virtual Environment & Dependencies

In the PythonAnywhere Bash console:

```bash
cd ~/Avaitor

# Create a virtual environment with Python 3.10 or 3.11
python3 -m venv .venv

# Activate and install dependencies
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ⚙️ Step 3: Configure `.env` File

In the Bash console, copy and verify your `.env`:

```bash
cp .env.example .env
nano .env
```

Ensure your token is set:
```ini
TELEGRAM_BOT_TOKEN=8737970445:AAF_AQwMPTlb7Z880YN8Q3UHl5RnSs40H3M
CHECK_INTERVAL_MINUTES=15
LOG_LEVEL=INFO
```
*(Press `Ctrl + O` then `Enter` to save, `Ctrl + X` to exit nano)*.

---

## 🌐 Choose Your Deployment Method

PythonAnywhere supports two great ways to run Berari:

---

### Option A: Web App + Webhook (Recommended for Free Accounts)
*This gives you both a live web status dashboard at `https://<yourusername>.pythonanywhere.com` AND interactive Telegram bot replies.*

1. **Go to the "Web" tab** on PythonAnywhere.
2. Click **Add a new web app**.
3. Choose **Manual configuration** and select **Python 3.10** (or 3.11).
4. In the Web tab configuration page:
   * **Source code:** `/home/<yourusername>/Avaitor`
   * **Working directory:** `/home/<yourusername>/Avaitor`
   * **Virtualenv:** `/home/<yourusername>/Avaitor/.venv`
5. Click on the link next to **WSGI configuration file** to edit it. Replace the contents with:
   ```python
   import sys
   from pathlib import Path

   project_home = '/home/<yourusername>/Avaitor'
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   from wsgi import application
   ```
   *(Replace `<yourusername>` with your actual PythonAnywhere username!)* Click **Save**.
6. Back on the Web tab, click **Reload <yourusername>.pythonanywhere.com**.
7. **Set Telegram Webhook:** Open this URL in your web browser:
   ```
   https://api.telegram.org/bot8737970445:AAF_AQwMPTlb7Z880YN8Q3UHl5RnSs40H3M/setWebhook?url=https://<yourusername>.pythonanywhere.com/webhook
   ```
   You will see: `{"ok":true,"result":true,"description":"Webhook was set"}`.
8. **Automate the Scraper:**
   * Go to the **Tasks** tab on PythonAnywhere.
   * Under **Scheduled tasks**, add a new task:
     * **Time:** Set your preferred run hour (e.g., daily or hourly).
     * **Command:** `/home/<yourusername>/Avaitor/.venv/bin/python /home/<yourusername>/Avaitor/run_task.py`
     * Click **Create**.

---

### Option B: "Always-On Task" (Paid / Hacker Plan $5/mo)
*If you have a paid PythonAnywhere plan with "Always-on tasks", you can run the bot 24/7 with long-polling just like on a local machine:*

1. Go to the **Tasks** tab.
2. In the **Always-on tasks** section, enter:
   ```bash
   /home/<yourusername>/Avaitor/.venv/bin/python /home/<yourusername>/Avaitor/bot.py
   ```
3. Click **Create**.
4. The bot is now permanently running in the background 24/7!

---

## 🔍 Testing on PythonAnywhere

In the Bash console, verify everything works with a single command:

```bash
cd ~/Avaitor
.venv/bin/python run_task.py
```

You should see:
```
[INFO] Berari: Starting scan for Ethiopian Airlines career openings...
[INFO] Berari: Task finished successfully.
```
