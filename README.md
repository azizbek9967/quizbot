# Telegram Bot for Render Deployment

This folder contains all the necessary files to deploy your Telegram bot to Render as a Background Worker so it runs 24/7 without needing your local machine (`localhost`).

## Files Included:
- `bot.py`: The Python Telegram bot script using `python-telegram-bot`.
- `requirements.txt`: Python package dependencies.
- `render.yaml`: Render Blueprint configuration file.

---

## How to Deploy to Render:

### Step 1: Push Code to GitHub
1. Create a new repository on GitHub (e.g., `my-telegram-bot`).
2. Push the contents of this folder (`bot.py`, `requirements.txt`, `render.yaml`) to the main branch of your GitHub repository.

### Step 2: Deploy on Render
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New** -> **Blueprint**.
3. Connect your GitHub repository (`my-telegram-bot`).
4. Render will automatically detect the `render.yaml` file.
5. Click **Apply**.

### Step 3: Set Your Environment Variable
1. In your Render Dashboard, go to your newly created `telegram-bot` worker service.
2. Go to **Environment**.
3. Add an Environment Variable:
   - **Key**: `TELEGRAM_TOKEN`
   - **Value**: Your actual Telegram Bot API token (from `@BotFather`).
4. Click **Save Changes** (Render will automatically redeploy with the token).

Your bot is now live and running 24/7 on Render!
