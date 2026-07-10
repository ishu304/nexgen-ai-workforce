# 📊 Data Analyst Toolkit

**A free, privacy-focused, local-first data cleaning & analytics tool.**
No sign-up. No cloud. No tracking. Your data never leaves your machine.

Built with Streamlit, it turns messy CSV/Excel files into clean,
chartable, insight-rich datasets — entirely offline.

---

## Why this tool?

Most "free" analytics tools quietly upload your data to someone else's
server. This one doesn't — it can't, because there isn't one. Everything
runs locally and everything is stored in plain JSON files on your own
computer.

- 🔒 **100% local & private** — no account, no internet connection required to use it
- 🧹 **One-click cleaning** — drop nulls, dedupe, trim whitespace automatically
- 🔗 **Merge multiple files** — stack rows or join columns side-by-side
- 🤖 **Auto Insights** — instant, rule-based summary of your data (types, stats, outliers, correlations, top categories) — no external AI call needed
- 📈 **Interactive charts** — Bar, Pie, Line, Area (Plotly), with automatic "Others" grouping so charts stay readable even with 50+ categories
- ✍️ **Manual data entry** — build a dataset from scratch and edit rows in a spreadsheet-style table
- ⬇️ **Export anytime** — CSV or Excel, no lock-in

## Features at a Glance

- **Dashboard** — datasets saved, total rows processed, last activity
- **Analytics** — upload, clean, merge, auto-insights, chart, export
- **Data Entry** — type in data directly, no file needed
- **Settings** — manage your local password

## Getting Started

```bash
git clone <your-repo-url>
cd bi_dashboard
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run main.py
```

First run: no profile exists yet, so the app shows a one-time "Set up
your local profile" screen — pick a username, name, and password.
After that, it's a normal login screen.

## Project Structure

```
bi_dashboard/
├── main.py               # Streamlit app — Dashboard, Analytics, Data Entry, Settings
├── data_handler.py        # JSON persistence, cleaning, merge, export, insights
├── security.py             # Password hashing (SHA-256 + salt)
├── requirements.txt
└── data/
    ├── users.json          # Your local profile (name, hashed password)
    └── processed_data.json # Your saved/cleaned/manually-entered datasets
```

## Data & Privacy

- All your data lives in `data/users.json` and `data/processed_data.json`
  — plain JSON files next to the app, on your machine only.
- Passwords are never stored in plain text (salted SHA-256 hash).
- Back up your work by copying the `data/` folder. That's it — no
  database, no server, nothing to migrate.

## Feedback & Support

This is an early, free release — bug reports and feature requests are
very welcome. Contact support at **feedback.ishupal@gmail.com**, or use
the **💬 Feedback / Support** button in the app sidebar — it opens your
default email app with the address, subject, and a short template
already filled in (app version, OS, Python version, feedback type,
description, steps to reproduce).

If something breaks, click **📋 Copy Error Details** in the sidebar
first — it copies the latest error (or basic diagnostic info if there
isn't one) to your clipboard so you can paste it straight into the
email. No dataset content or personal files are ever included.

## Roadmap

The free local edition will keep improving. Planned additions:

- Search / filter / sort within the data table
- Column rename + type conversion (text → number/date)
- Data validation rules for entry forms (required fields, number ranges)
- PDF export of dashboard summaries

Longer-term, optional **Pro** features (Advanced Analytics, Cloud
Auto-Backup, Team Collaboration) are being explored for users who want
more than a local single-user setup — the sidebar has a placeholder for
this, but everything usable today is, and will remain, free.

## License

Add your preferred license here (e.g. MIT) before publishing.

---

*Built with Streamlit, pandas, and Plotly.*
