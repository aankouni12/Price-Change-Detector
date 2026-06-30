from database import get_connection
from rapidfuzz import fuzz
from datetime import datetime
from statistics import mean, stdev

FUZZY_THRESHOLD = 85
MIN_OCCURRENCES = 3
INTERVAL_TOLERANCE_DAYS = 5
PRICE_INCREASE_TOLERANCE = 0.01


def load_transactions():
    """Pull all transactions from the DB, return as list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, category, amount, date, note FROM transactions")
    rows = cursor.fetchall()
    conn.close()

    transactions = []
    for row in rows:
        transactions.append({
            "id":       row[0],
            "type":     row[1],
            "category": row[2],
            "amount":   row[3],
            "date":     datetime.strptime(row[4], "%Y-%m-%d").date(),
            "merchant": row[5] or "",
        })
    return transactions


def normalize(merchant):
    import re
    STRIP_WORDS = {"COM", "US", "USA", "LLC", "INC", "CORP"}
    merchant = merchant.upper().strip()
    merchant = re.sub(r"[^A-Z\s]", " ", merchant)
    tokens = [t for t in merchant.split() if t not in STRIP_WORDS]
    return " ".join(tokens).strip()


def group_by_merchant(transactions):
    """
    Groups transactions by merchant using fuzzy string matching.
    Returns a list of groups — each group is a list of transactions
    from the same merchant.

    How it works:
    - For each transaction, compare its merchant name to the first
      transaction in every existing group
    - If similarity score >= FUZZY_THRESHOLD, it belongs to that group
    - If no group matches, start a new group
    """
    groups = []

    for t in transactions:
        if not t["merchant"]:
            continue

        placed = False
        for group in groups:
            representative = normalize(group[0]["merchant"])
            candidate = normalize(t["merchant"])
            score = fuzz.token_sort_ratio(representative, candidate)

            if score >= FUZZY_THRESHOLD:
                group.append(t)
                placed = True
                break

        if not placed:
            groups.append([t])

    return groups


def is_recurring(group):
    """
    Returns True if a merchant group looks like a recurring subscription.

    Checks:
    1. Minimum number of charges (avoids flagging a one-off coincidence)
    2. Consistent intervals between charges (monthly = ~30 days)
    3. Low variance in those intervals (high variance = not a subscription)
    """
    if len(group) < MIN_OCCURRENCES:
        return False

    sorted_group = sorted(group, key=lambda t: t["date"])
    dates = [t["date"] for t in sorted_group]
    gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates) - 1)]

    avg_gap = mean(gaps)

    # Gap should be roughly monthly (20-45 days covers weekly, biweekly, monthly)
    if not (20 <= avg_gap <= 45):
        return False

    # Gaps should be consistent — high stdev means irregular charges
    if len(gaps) > 1 and stdev(gaps) > INTERVAL_TOLERANCE_DAYS:
        return False

    return True


def detect_price_change(group):
    """
    For a confirmed recurring group, compares the most recent charge
    to the historical baseline (average of all previous charges).

    Returns a dict with:
    - flagged: True if a price increase was detected
    - merchant: merchant name
    - baseline: average of all charges except the latest
    - latest: the most recent charge amount
    - difference: how much it went up
    """
    sorted_group = sorted(group, key=lambda t: t["date"])
    history = sorted_group[:-1]   # everything except the latest charge
    latest = sorted_group[-1]

    baseline = mean(t["amount"] for t in history)
    difference = latest["amount"] - baseline

    flagged = latest["amount"] > baseline * (1 + PRICE_INCREASE_TOLERANCE)

    return {
        "flagged":   flagged,
        "merchant":  latest["merchant"],
        "baseline":  round(baseline, 2),
        "latest":    latest["amount"],
        "difference": round(difference, 2),
        "date":      latest["date"],
    }


def run_detection():
    """
    Full pipeline:
    1. Load transactions from DB
    2. Group by merchant
    3. Filter to recurring groups only
    4. Check each recurring group for price changes
    5. Return list of flagged results
    """
    transactions = load_transactions()
    groups = group_by_merchant(transactions)

    flagged = []
    for group in groups:
        if is_recurring(group):
            result = detect_price_change(group)
            if result["flagged"]:
                flagged.append(result)

    return flagged


if __name__ == "__main__":
    results = run_detection()

    if not results:
        print("No price changes detected.")
    else:
        print(f"\n{len(results)} price change(s) detected:\n")
        for r in results:
            print(f"  {r['merchant']}")
            print(f"    Was:        ${r['baseline']:.2f}")
            print(f"    Now:        ${r['latest']:.2f}")
            print(f"    Increase:   ${r['difference']:.2f}")
            print(f"    Detected:   {r['date']}\n")