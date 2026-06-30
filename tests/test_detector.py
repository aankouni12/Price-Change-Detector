import pytest
from datetime import date
from detector import group_by_merchant, is_recurring, detect_price_change, run_detection


def make_transaction(merchant, amount, charge_date):
    return {
        "id":       1,
        "type":     "expense",
        "category": "subscription",
        "amount":   amount,
        "date":     charge_date,
        "merchant": merchant,
    }


def make_monthly_charges(merchant, amount, months=12, start=date(2025, 7, 1)):
    from datetime import timedelta
    charges = []
    current = start
    for _ in range(months):
        charges.append(make_transaction(merchant, amount, current))
        current += timedelta(days=30)
    return charges


def make_charges_with_increase(merchant, base_price, new_price, increase_month, months=12, start=date(2025, 7, 1)):
    from datetime import timedelta
    charges = []
    current = start
    for i in range(months):
        price = new_price if i >= increase_month else base_price
        charges.append(make_transaction(merchant, price, current))
        current += timedelta(days=30)
    return charges


def test_same_merchant_grouped_together():
    transactions = [
        make_transaction("NETFLIX.COM",       15.49, date(2025, 7, 1)),
        make_transaction("NETFLIX 855-100",   15.49, date(2025, 8, 1)),
        make_transaction("NETFLIX",           15.49, date(2025, 9, 1)),
    ]
    groups = group_by_merchant(transactions)
    assert len(groups) == 1


def test_different_merchants_not_grouped():
    transactions = [
        make_transaction("NETFLIX.COM", 15.49, date(2025, 7, 1)),
        make_transaction("SPOTIFY USA", 9.99,  date(2025, 7, 1)),
    ]
    groups = group_by_merchant(transactions)
    assert len(groups) == 2


def test_monthly_subscription_detected_as_recurring():
    group = make_monthly_charges("NETFLIX.COM", 15.49, months=12)
    assert is_recurring(group) == True


def test_too_few_charges_not_recurring():
    group = make_monthly_charges("NETFLIX.COM", 15.49, months=2)
    assert is_recurring(group) == False


def test_irregular_charges_not_recurring():
    from datetime import timedelta
    import random
    random.seed(42)
    charges = []
    current = date(2025, 7, 1)
    for _ in range(8):
        charges.append(make_transaction("AMAZON MKTP US", 47.23, current))
        current += timedelta(days=random.randint(1, 60))
    assert is_recurring(charges) == False


def test_price_increase_flagged():
    group = make_charges_with_increase(
        "NETFLIX.COM", base_price=15.49, new_price=17.99, increase_month=8
    )
    result = detect_price_change(group)
    assert result["flagged"] == True
    assert result["latest"] == 17.99


def test_stable_price_not_flagged():
    group = make_monthly_charges("SPOTIFY USA", 9.99, months=12)
    result = detect_price_change(group)
    assert result["flagged"] == False


def test_price_decrease_not_flagged():
    group = make_charges_with_increase(
        "SOME SERVICE", base_price=15.49, new_price=12.99, increase_month=8
    )
    result = detect_price_change(group)
    assert result["flagged"] == False


def test_full_pipeline_catches_correct_merchants():
    results = run_detection()
    flagged_merchants = [r["merchant"] for r in results]
    assert "NETFLIX.COM" in flagged_merchants
    assert "PLANET FITNESS" in flagged_merchants
    assert "SPOTIFY USA" not in flagged_merchants
    assert "YOUTUBE PREMIUM" not in flagged_merchants


def test_full_pipeline_flags_exactly_two():
    results = run_detection()
    assert len(results) == 2