import random
from datetime import date, timedelta
from database import get_connection

SUBSCRIPTIONS = [
    {
        "merchant": "NETFLIX.COM",
        "base_price": 15.49,
        "price_increase_month": 8,
        "new_price": 17.99,
    },
    {
        "merchant": "SPOTIFY USA",
        "base_price": 9.99,
        "price_increase_month": None,
        "new_price": None,
    },
    {
        "merchant": "PLANET FITNESS",
        "base_price": 29.99,
        "price_increase_month": 5,
        "new_price": 34.99,
    },
    {
        "merchant": "YOUTUBE PREMIUM",
        "base_price": 13.99,
        "price_increase_month": None,
        "new_price": None,
    },
]

MONTHS = 12
START_DATE = date(2025, 7, 1)


def generate_subscription_transactions():
    transactions = []
    for sub in SUBSCRIPTIONS:
        current_date = START_DATE
        for month_index in range(MONTHS):
            if sub["price_increase_month"] is not None and month_index >= sub["price_increase_month"]:
                price = sub["new_price"]
            else:
                price = sub["base_price"]

            variance = random.randint(-2, 2)
            charge_date = current_date + timedelta(days=variance)

            transactions.append({
                "type": "expense",
                "category": "subscription",
                "amount": price,
                "date": str(charge_date),
                "note": sub["merchant"],
            })

            current_date += timedelta(days=30)
    return transactions


def generate_noise_transactions(count=150):
    noise_merchants = [
        ("MCDONALDS #4821",     "food",       8.00,  15.00),
        ("SHELL OIL 57442",     "gas",        40.00, 80.00),
        ("KROGER #0391",        "groceries",  30.00, 120.00),
        ("AMAZON MKTP US",      "shopping",   5.00,  200.00),
        ("WALMART SUPERCENTER", "shopping",   20.00, 150.00),
        ("CHIPOTLE 1204",       "food",       10.00, 20.00),
        ("BP#9637281",          "gas",        35.00, 75.00),
        ("MEIJER #054",         "groceries",  25.00, 90.00),
    ]

    end_date = START_DATE + timedelta(days=365)
    date_range_days = (end_date - START_DATE).days

    transactions = []
    for _ in range(count):
        merchant, category, min_amt, max_amt = random.choice(noise_merchants)
        random_date = START_DATE + timedelta(days=random.randint(0, date_range_days))
        amount = round(random.uniform(min_amt, max_amt), 2)

        transactions.append({
            "type": "expense",
            "category": category,
            "amount": amount,
            "date": str(random_date),
            "note": merchant,
        })
    return transactions


def insert_transactions(transactions):
    conn = get_connection()
    cursor = conn.cursor()
    for t in transactions:
        cursor.execute("""
            INSERT INTO transactions (type, category, amount, date, note)
            VALUES (?, ?, ?, ?, ?)
        """, (t["type"], t["category"], t["amount"], t["date"], t["note"]))
    conn.commit()
    conn.close()
    print(f"Inserted {len(transactions)} transactions.")


def clear_existing_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
    print("Cleared existing transactions.")


def print_ground_truth():
    print("\n--- Ground truth planted ---")
    for sub in SUBSCRIPTIONS:
        if sub["price_increase_month"] is not None:
            print(
                f"  {sub['merchant']}: ${sub['base_price']:.2f} → "
                f"${sub['new_price']:.2f} starting at charge #{sub['price_increase_month'] + 1}"
            )
        else:
            print(f"  {sub['merchant']}: stable at ${sub['base_price']:.2f} — should NOT be flagged")


if __name__ == "__main__":
    clear_existing_data()
    sub_transactions = generate_subscription_transactions()
    noise_transactions = generate_noise_transactions(count=150)
    all_transactions = sub_transactions + noise_transactions
    insert_transactions(all_transactions)
    print_ground_truth()
    print(f"\nTotal transactions in DB: {len(all_transactions)}")