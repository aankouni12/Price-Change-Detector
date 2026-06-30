import subprocess
from database import initialize_db
from tracker import add_transaction, view_transactions, delete_transaction, monthly_summary
from detector import run_detection
from alerts import send_all_alerts

def main():
    initialize_db()

    while True:
        print("\n===== Finance Tracker =====")
        print("1. Add transaction")
        print("2. View all transactions")
        print("3. Delete a transaction")
        print("4. Monthly summary")
        print("5. Run detection & send alerts")
        print("6. Open dashboard")
        print("7. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            type = input("Type (income/expense): ").lower()
            category = input("Category (e.g. food, salary, rent): ")
            amount = float(input("Amount: "))
            note = input("Note (optional, press Enter to skip): ")
            add_transaction(type, category, amount, note)

        elif choice == "2":
            view_transactions()

        elif choice == "3":
            transaction_id = int(input("Enter transaction ID to delete: "))
            delete_transaction(transaction_id)

        elif choice == "4":
            monthly_summary()

        elif choice == "5":
            print("\Running detection...")
            results = run_detection()
            if not results:
                print("No price changes detected.")
            else:
                print(f"{len(results)} price change(s) detected:")
                for r in results:
                    print(f"  {r['merchant']}: ${r['baseline']:.2f} → ${r['latest']:.2f}")
                recipient = input("\nEnter your email to receive alerts: ")
                confirm = input(f"Send alerts to {recipient}? (y/n): ")
                if confirm.lower() == "y":
                    send_all_alerts(results, recipient=recipient)

        elif choice == "6":
            print("\nLaunching dashboard — press Ctrl+C here to stop it.")
            subprocess.run(["streamlit", "run", "dashboard.py"])

        elif choice == "7":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()