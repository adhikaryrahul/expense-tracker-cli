#Expense Tracker


import json
import math
import os
import re
import tempfile

from decimal import Decimal, InvalidOperation
from datetime import datetime, date


FILENAME = "expenses.json"

CATEGORIES = ["Food", "Transport", "Utilities", "Other"]

MAX_AMOUNT = Decimal("100000000000")
MAX_SUBCATEGORY_LEN = 40

# Accepts normal numbers and correctly formatted comma-separated numbers.
# Maximum two decimal places.
AMOUNT_PATTERN = re.compile(
    r"^(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$"
)


# --------------------------------------------------
# 1. AMOUNT VALIDATION
# --------------------------------------------------

def parse_amount(value):
    """Validate and convert an amount into Decimal."""

    text = value.strip()

    if not AMOUNT_PATTERN.fullmatch(text):
        raise ValueError("Invalid amount format.")

    try:
        amount = Decimal(text.replace(",", ""))
    except InvalidOperation:
        raise ValueError("Invalid amount.")

    if not amount.is_finite():
        raise ValueError("Amount must be a finite number.")

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    if amount > MAX_AMOUNT:
        raise ValueError("Amount is too large.")

    return amount.quantize(Decimal("0.01"))


# --------------------------------------------------
# 2. DATE VALIDATION
# --------------------------------------------------

def validate_date(text):
    """Check whether a date is valid and not in the history or future."""

    try:
        parsed = datetime.strptime(text, "%d-%m-%Y").date()
    except (ValueError, TypeError):
        return None

    # Require the exact DD-MM-YYYY format.
    if parsed.strftime("%d-%m-%Y") != text:
        return None

    if parsed > date.today():
        return None

    return parsed


# --------------------------------------------------
# 3. LOAD EXPENSES
# --------------------------------------------------

def load_expenses(filename=FILENAME):
    """Load expenses and validate every record."""

    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            print("Invalid file structure. Starting with an empty list.")
            return []

        valid_expenses = []

        for item in data:

            if not isinstance(item, dict):
                continue

            raw_amount = item.get("amount")

            # Reject booleans because bool is a subclass of int.
            if isinstance(raw_amount, bool):
                continue

            if not isinstance(raw_amount, (int, float, str)):
                continue

            try:
                amount = Decimal(str(raw_amount))

                if (
                    not amount.is_finite()
                    or amount <= 0
                    or amount > MAX_AMOUNT
                ):
                    continue

            except (InvalidOperation, ValueError, TypeError):
                continue

            category = item.get("category", "Other")

            if not isinstance(category, str):
                continue

            category = category.strip()

            if category not in CATEGORIES:
                continue

            # Subcategories are allowed only for Other.
            sub = item.get("sub_category")

            if category == "Other" and sub is not None:

                sub = " ".join(str(sub).split())
                sub = sub[:MAX_SUBCATEGORY_LEN]

                if not any(ch.isalpha() for ch in sub):
                    sub = None

                if sub == "":
                    sub = None

            else:
                sub = None

            # Validate stored dates.
            dt_str = item.get("date")

            if not isinstance(dt_str, str):
                continue

            parsed_date = validate_date(dt_str)

            if parsed_date is None:
                continue

            valid_expenses.append({
                "amount": float(amount),
                "category": category,
                "sub_category": sub,
                "date": parsed_date.strftime("%d-%m-%Y")
            })

        return valid_expenses

    except FileNotFoundError:
        return []

    except (json.JSONDecodeError, OSError):
        print("Error reading the file. Starting with an empty list.")
        return []


# --------------------------------------------------
# 4. SAVE EXPENSES SAFELY
# --------------------------------------------------

def save_expenses(filename, expenses):
    """
    Save expenses using a temporary file.

    os.replace() replaces the old file only after
    the new file has been written successfully.
    """

    temp_path = None

    try:
        directory = os.path.dirname(os.path.abspath(filename))

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            delete=False
        ) as file:

            temp_path = file.name

            json.dump(
                expenses,
                file,
                indent=4,
                allow_nan=False
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, filename)
        return True

    except (OSError, TypeError, ValueError):
        print("Error: Could not save expenses to file.")
        return False

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# --------------------------------------------------
# 5. CATEGORY INPUT
# --------------------------------------------------

def ask_category():
    """Ask the user to select a valid category."""

    while True:

        print("\nCategories:")

        for number, name in enumerate(CATEGORIES, 1):
            print(f"  {number}. {name}")

        choice = input(
            f"Choose a category (1-{len(CATEGORIES)}): "
        ).strip()

        if choice.isdecimal() and 1 <= int(choice) <= len(CATEGORIES):
            return CATEGORIES[int(choice) - 1]

        print("Invalid choice. Please select a valid number.")


# --------------------------------------------------
# 6. SUBCATEGORY INPUT
# --------------------------------------------------

def ask_sub_category():
    """Ask for an optional subcategory."""

    while True:

        sub = input(
            "Specify Sub-Category (e.g., Hospital Charges, "
            "School Fees), or press Enter to skip: "
        ).strip()

        cleaned = " ".join(sub.split())

        if not cleaned:
            return None

        if not any(ch.isalpha() for ch in cleaned):
            print("Sub-category must contain at least one letter.")
            continue

        if len(cleaned) > MAX_SUBCATEGORY_LEN:
            print(
                f"Sub-category must not exceed "
                f"{MAX_SUBCATEGORY_LEN} characters."
            )
            continue

        return cleaned


# --------------------------------------------------
# 7. DATE INPUT
# --------------------------------------------------

def ask_date():
    """Ask for a valid non-historical or non-future date."""

    while True:

        text = input(
            "Enter date (DD-MM-YYYY), or press Enter for today: "
        ).strip()

        if not text:
            return date.today().strftime("%d-%m-%Y")

        parsed = validate_date(text)

        if parsed is None:
            print(
                "Invalid date. Enter a real date in "
                "DD-MM-YYYY format, not from the history or in the future.\n"
            )
            continue

        return parsed.strftime("%d-%m-%Y")


# --------------------------------------------------
# 8. ADD EXPENSE
# --------------------------------------------------

def add_expense(expenses, filename=FILENAME):
    """Collect, validate and save a new expense."""

    try:
        amount_input = input("Enter amount (₹): ")
        amount = parse_amount(amount_input)

    except ValueError:
        print("Invalid amount. Enter a positive number with up to "
              "two decimal places.")
        return

    category = ask_category()

    sub_category = (
        ask_sub_category()
        if category == "Other"
        else None
    )

    date_text = ask_date()

    expense = {
        "amount": float(amount),
        "category": category,
        "sub_category": sub_category,
        "date": date_text
    }

    expenses.append(expense)

    # Save immediately to reduce the risk of losing new entries.
    if save_expenses(filename, expenses):
        print("Expense added and saved successfully!")

    else:
        # Roll back the addition if saving fails.
        expenses.pop()
        print("Expense was not added because saving failed.")


# --------------------------------------------------
# 9. FORMAT CATEGORY LABEL
# --------------------------------------------------

def format_category_label(expense):
    """Display category and subcategory together."""

    cat = expense.get("category", "Other")
    sub = expense.get("sub_category")

    if cat == "Other" and sub:
        return f"{cat} ({sub})"

    return cat


# --------------------------------------------------
# 10. PRINT EXPENSE TABLE
# --------------------------------------------------

def print_expenses_table(
    expenses,
    title="--- All Expenses ---",
    start_index=1
):
    """Display expenses in a formatted table."""

    labels = [
        format_category_label(exp)
        for exp in expenses
    ]

    cat_width = max(
        [len("Category"), 25] +
        [len(label) for label in labels]
    )

    line_len = 6 + 3 + 12 + 3 + cat_width + 3 + 12

    print(f"\n{title}")

    print(
        f"{'Index':<6} | "
        f"{'Date':<12} | "
        f"{'Category':<{cat_width}} | "
        f"{'Amount (₹)':<12}"
    )

    print("-" * line_len)

    for idx, (exp, label) in enumerate(
        zip(expenses, labels),
        start_index
    ):

        print(
            f"{idx:<6} | "
            f"{exp.get('date', 'N/A'):<12} | "
            f"{label:<{cat_width}} | "
            f"{exp['amount']:<12.2f}"
        )


# --------------------------------------------------
# 11. VIEW EXPENSES
# --------------------------------------------------

def view_expenses(expenses):
    """Display all expenses."""

    if not expenses:
        print("No expenses recorded yet.")
        return

    print_expenses_table(
        expenses,
        "--- All Expenses ---"
    )


# --------------------------------------------------
# 12. CALCULATE TOTAL
# --------------------------------------------------

def calculate_total(expenses):
    """Calculate total spending accurately using Decimal."""

    if not expenses:
        print("No expenses recorded yet.")
        return

    print_expenses_table(
        expenses,
        "--- Total Spending Breakdown ---"
    )

    total = sum(
        (Decimal(str(exp["amount"])) for exp in expenses),
        Decimal("0")
    )

    print(f"\nTotal amount spent: ₹{total:.2f}")


# --------------------------------------------------
# 13. SPENDING BY CATEGORY
# --------------------------------------------------

def spending_by_category(expenses):
    """Group and display expenses by category."""

    if not expenses:
        print("No expenses recorded yet.")
        return

    grouped = {}

    for idx, exp in enumerate(expenses, 1):

        label = format_category_label(exp)

        grouped.setdefault(label, []).append((idx, exp))

    all_labels = [
        format_category_label(exp)
        for exp in expenses
    ]

    cat_width = max(
        [len("Category"), 25] +
        [len(label) for label in all_labels]
    )

    line_len = 6 + 3 + 12 + 3 + cat_width + 3 + 12

    print("\n--- Spending by Category ---")

    print(
        f"{'Index':<6} | "
        f"{'Date':<12} | "
        f"{'Category':<{cat_width}} | "
        f"{'Amount (₹)':<12}"
    )

    print("-" * line_len)

    for label, items in grouped.items():

        for idx, exp in items:

            print(
                f"{idx:<6} | "
                f"{exp.get('date', 'N/A'):<12} | "
                f"{label:<{cat_width}} | "
                f"{exp['amount']:<12.2f}"
            )

        print("-" * line_len)

    grand_total = sum(
        (Decimal(str(exp["amount"])) for exp in expenses),
        Decimal("0")
    )

    print(f"Total amount spent: ₹{grand_total:.2f}")


# --------------------------------------------------
# 14. DELETE ALL EXPENSES
# --------------------------------------------------

def delete_all_expenses(expenses, filename=FILENAME):
    """Delete all expenses safely."""

    if not expenses:
        print("There are no expenses to delete.")
        return

    confirm = input(
        "Are you sure you want to delete ALL expenses? (y/n): "
    ).strip().lower()

    if confirm not in ("y", "yes"):
        print("Deletion cancelled.")
        return

    # Save the empty list before clearing memory.
    if save_expenses(filename, []):

        expenses.clear()

        print("All expenses have been deleted.")

    else:
        print("Deletion failed. Your existing expenses are preserved.")


# --------------------------------------------------
# 15. MAIN PROGRAM
# --------------------------------------------------

def main():
    """Main program loop."""

    expenses = load_expenses(FILENAME)

    while True:

        print("\n=== Expense Tracker Menu ===")

        print("1. Add Expense")
        print("2. View All Expenses")
        print("3. Calculate Total Spending")
        print("4. Spending by Category")
        print("5. Delete All Expenses")
        print("6. Save and Exit")

        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":

            add_expense(expenses, FILENAME)

        elif choice == "2":

            view_expenses(expenses)

        elif choice == "3":

            calculate_total(expenses)

        elif choice == "4":

            spending_by_category(expenses)

        elif choice == "5":

            delete_all_expenses(expenses, FILENAME)

        elif choice == "6":

            if save_expenses(FILENAME, expenses):

                print(
                    "Expenses saved successfully. "
                    "Have a good day. Bye!"
                )

                break

            print(
                "Your expenses were NOT saved. "
                "Fix the problem and try again."
            )

        else:

            print(
                "Invalid choice. "
                "Please enter a number between 1 and 6."
            )


# --------------------------------------------------
# 16. PROGRAM ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    try:
        main()

    except (KeyboardInterrupt, EOFError):

        print(
            "\nInterrupted. "
            "Previously saved expenses are preserved."
        )

#Expense Tracker Ends
