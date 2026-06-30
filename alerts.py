import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
ALERT_RECIPIENT = os.environ.get("ALERT_RECIPIENT", GMAIL_ADDRESS)


def send_price_alert(merchant, baseline, latest, difference, detected_date, recipient=None):
    if recipient is None:
        recipient = ALERT_RECIPIENT

    subject = f"Price increase detected: {merchant}"

    body = f"""
Hi,

Your subscription price tracker detected a change:

  Merchant:   {merchant}
  Previous:   ${baseline:.2f}
  New price:  ${latest:.2f}
  Increase:   ${difference:.2f}
  Detected:   {detected_date}

— Finance Tracker
"""

    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)

    print(f"Alert sent to {recipient} for {merchant}.")


def send_all_alerts(detection_results, recipient=None):
    if not detection_results:
        print("No alerts to send.")
        return

    for result in detection_results:
        send_price_alert(
            merchant=result["merchant"],
            baseline=result["baseline"],
            latest=result["latest"],
            difference=result["difference"],
            detected_date=result["date"],
            recipient=recipient,
        )


if __name__ == "__main__":
    from detector import run_detection
    results = run_detection()
    send_all_alerts(results)