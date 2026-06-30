import streamlit as st
import pandas as pd
from detector import load_transactions, group_by_merchant, is_recurring, detect_price_change, run_detection
from alerts import send_all_alerts

st.set_page_config(page_title="Finance Tracker", page_icon="💳", layout="wide")

st.title("💳 Subscription Monitor")
st.caption("Automatic subscription tracking and price-change detection")

transactions = load_transactions()
groups = group_by_merchant(transactions)
recurring_groups = [g for g in groups if is_recurring(g)]
all_results = [detect_price_change(g) for g in recurring_groups]
flagged = [r for r in all_results if r["flagged"]]

col1, col2, col3 = st.columns(3)
col1.metric("Active Subscriptions", len(all_results))
col2.metric("Monthly Spend", f"${sum(r['latest'] for r in all_results):.2f}")
col3.metric("Price Alerts", len(flagged))

if flagged:
    st.subheader("⚠️ Price Alerts")
    for r in flagged:
        st.warning(
            f"**{r['merchant']}** increased from "
            f"${r['baseline']:.2f} to ${r['latest']:.2f} "
            f"(+${r['difference']:.2f})"
        )

st.subheader("All Subscriptions")
df = pd.DataFrame([{
    "Merchant":      r["merchant"],
    "Current Price": f"${r['latest']:.2f}",
    "Baseline":      f"${r['baseline']:.2f}",
    "Status":        "⚠️ Increased" if r["flagged"] else "✅ Stable",
    "Last Detected": str(r["date"]),
} for r in all_results])
st.dataframe(df, use_container_width=True)

st.subheader("Monthly Spend by Subscription")
chart_data = pd.DataFrame({
    "Merchant": [r["merchant"] for r in all_results],
    "Amount":   [r["latest"] for r in all_results],
}).set_index("Merchant")
st.bar_chart(chart_data)

st.subheader("Actions")
if st.button("🔍 Run Detection & Send Email Alerts"):
    with st.spinner("Running detection..."):
        results = run_detection()
        send_all_alerts(results)
    if results:
        st.success(f"Sent {len(results)} alert(s) — check your inbox.")
    else:
        st.info("No price changes detected — no emails sent.")