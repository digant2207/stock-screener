# 📈 CAR + 30/50/200 DMA Super Breakout Stock Screener

An automated stock breakout scanner for Indian stocks (NSE & BSE) using Yahoo Finance data. It identifies stocks where:
- Current Market Price (CMP) > 30 DMA
- CMP > 50 DMA
- CMP > 200 DMA
- Cumulative Average (`CAR`) from 52-Week High is monotonically increasing over the last 10 trading days.

Automatically runs **daily at 7:00 PM IST (13:30 UTC)** via **GitHub Actions** and emails the results with an attached `Final_Breakout_List.xlsx` report directly to your Gmail inbox!

---

## 🚀 Setup Instructions for GitHub (`digant2207`)

### Step 1: Create Repository on GitHub
1. Go to [GitHub New Repository](https://github.com/new).
2. Repository Name: `stock-screener`
3. Description: `CAR + 30/50/200 DMA Stock Screener with Daily 7 PM Gmail Reports`
4. Set to **Public** or **Private**.
5. Click **Create repository**.

### Step 2: Push Code to GitHub
Run the following commands in your local project folder:
```bash
git remote add origin https://github.com/digant2207/stock-screener.git
git branch -M main
git push -u origin main
```

### Step 3: Configure GitHub Secrets for Daily 7:00 PM Emails
To enable automated daily 7:00 PM email dispatch to your Gmail:
1. Go to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret** and add the following 4 secrets:

| Secret Name | Description / Value |
|---|---|
| `GMAIL_USER` | Your Gmail address (e.g., `yourname@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Your 16-character Gmail App Password |
| `RECIPIENT_EMAIL` | (Optional) Destination Gmail address (defaults to `GMAIL_USER`) |
| `GOOGLE_SHEET_URL` | Your Google Sheet URL containing stock tickers in Column A |

> 💡 **How to generate a Gmail App Password**:
> 1. Go to Google Account Settings -> Security -> Enable 2-Step Verification.
> 2. Search for **App Passwords**.
> 3. Create a password named "Stock Screener" and copy the 16-character code into GitHub Secret `GMAIL_APP_PASSWORD`.

---

## 💻 Local Web Dashboard

You can also run the interactive web app locally anytime:

```bash
# Activate virtualenv and install requirements
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Run Web App
python app.py
```

Open `http://localhost:5000` in your browser.


<!-- Updated: 2026-08-17 -->