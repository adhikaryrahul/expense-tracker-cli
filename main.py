# Expense Tracker Program Begins Here...

import json
import math
import os

FILENAME = "expenses.json"

def load_expenses(filename=FILENAME):
    """Load expenses from a JSON file with exception handling."""
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Error reading the file. Starting with an empty expense list.")
        return []

def save_expenses(filename, expenses):
    """Save the current list of expenses to a JSON file."""
    try:
        with open(filename, "w") as file:
            json.dump(expenses, file, indent=4)
        return True
    except IOError:
        print("Error: Could not save expenses to file.")
        return False

def add_expense(expenses):
    """Prompt user for details and add a new expense."""
    try:
        amount_input = input("Enter amount (₹): ").strip()
        amount = float(amount_input)
        if not math.isfinite(amount):
            print("Invalid amount. Please enter a valid number.")
            return
        if amount < 0:
            print("Amount cannot be negative.")
            return
    except ValueError:
        print("Invalid amount. Please enter a valid number.")
        return

    category = input("Enter category (e.g., Food, Transport, Utilities): ").strip()
    date = input("Enter date (YYYY-MM-DD): ").strip()

    expense = {
        "amount": amount,
        "category": category if category else "Uncategorized",
        "date": date if date else "Unknown"
    }
    
    expenses.append(expense)
    print("Expense added successfully!")

def view_expenses(expenses):
    """Display all recorded expenses in a formatted table."""
    if not expenses:
        print("No expenses recorded yet.")
        return
    
    print("\n--- All Expenses ---")
    print(f"{'Index':<6} | {'Date':<12} | {'Category':<15} | {'Amount (₹)':<10}")
    print("-" * 50)
    for idx, exp in enumerate(expenses, 1):
        print(f"{idx:<6} | {exp['date']:<12} | {exp['category']:<15} | {exp['amount']:<10.2f}")

def calculate_total(expenses):
    """Calculate and display total spending."""
    total = sum(exp["amount"] for exp in expenses)
    print(f"\nTotal Spending: ₹{total:.2f}")

def spending_by_category(expenses):
    """Group and calculate total spending by each category."""
    if not expenses:
        print("No expenses recorded yet.")
        return

    category_totals = {}
    for exp in expenses:
        cat = exp["category"]
        category_totals[cat] = category_totals.get(cat, 0.0) + exp["amount"]

    print("\n--- Spending by Category ---")
    for cat, total in category_totals.items():
        print(f"{cat}: ₹{total:.2f}")

def main():
    """Main program loop."""
    expenses = load_expenses()
    
    while True:
        print("\n=== Expense Tracker Menu ===")
        print("1. Add Expense")
        print("2. View All Expenses")
        print("3. Calculate Total Spending")
        print("4. Spending by Category")
        print("5. Save and Exit")
        
        choice = input("Choose an option (1-5): ").strip()
        
        if choice == "1":
            add_expense(expenses)
        elif choice == "2":
            view_expenses(expenses)
        elif choice == "3":
            calculate_total(expenses)
        elif choice == "4":
            spending_by_category(expenses)
        elif choice == "5":
            if save_expenses(FILENAME, expenses):
                print("Expenses saved successfully. Goodbye!")
                break
            print("Your expenses were NOT saved. Fix the problem and try again.")
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nInterrupted. Unsaved expenses were not saved.")

# Expense Tracker Program Ends Here...