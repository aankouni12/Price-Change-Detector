# Finance Tracker + Subscription Monitor

A command-line and web-based personal finance tracker built with Python and SQLite, with automatic subscription detection and price-change alerts.

## Features
- Add, view, and delete income/expense transactions
- Monthly summary with net balance
- Automatic recurring subscription detection using fuzzy merchant matching
- Price-change detection — alerts you when a subscription quietly increases
- Email alerts via Gmail when a price change is detected
- Streamlit web dashboard showing all subscriptions, alerts, and spend chart

## Tech Stack
- Python
- SQLite
- rapidfuzz (fuzzy merchant name matching)
- Streamlit (web dashboard)
- smtplib (Gmail email alerts)
- pytest + GitHub Actions (testing and CI/CD)

## Project Structure

    finance-tracker/
    ├── database.py        # DB connection and initialization
    ├── tracker.py         # Core CRUD operations
    ├── detector.py        # Recurring charge and price-change detection
    ├── alerts.py          # Gmail email alert sending
    ├── dashboard.py       # Streamlit web dashboard
    ├── generate_data.py   # Synthetic data generator (for testing)
    ├── main.py            # CLI entry point
    └── tests/
        ├── test_tracker.py
        └── test_detector.py

## How to Run

1. Clone the repo and set up a virtual environment

        git clone https://github.com/yourusername/finance-tracker.git
        cd finance-tracker
        python -m venv venv
        venv\Scripts\activate
        pip install -r requirements.txt

2. Set up Gmail credentials

    Create a .env file in the project root:

        GMAIL_ADDRESS=youremail@gmail.com
        GMAIL_APP_PASSWORD=your16charapppassword
        ALERT_RECIPIENT=recipientemail@anywhere.com

    Generate an App Password at myaccount.google.com/apppasswords (requires 2-Step Verification).

3. Initialize the database and generate synthetic data

        python -c "from database import initialize_db; initialize_db()"
        python generate_data.py

4. Run the CLI

        python main.py

5. Or launch the dashboard directly

        streamlit run dashboard.py

## Running Tests

    pytest tests/ -v

## How Detection Works

1. Transactions are grouped by merchant using fuzzy string matching — "NETFLIX.COM" and "NETFLIX 855-100" are recognized as the same merchant
2. Groups are checked for recurring patterns (consistent ~30 day intervals, minimum 3 occurrences)
3. Confirmed recurring charges are compared against their historical baseline — if the latest charge is higher, an email alert is sent to the configured recipient