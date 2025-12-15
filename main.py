import csv
import os
from datetime import datetime

from flask import Flask, redirect, render_template, request

app = Flask(__name__)

# CSV file to store expenses
EXPENSES_FILE = 'expenses.csv'

def init_csv():
    """Create CSV file if it doesn't exist"""
    if not os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'amount', 'description', 'category'])

@app.route("/")
def home():
    return render_template('home.html')

@app.route('/expenses')
def expenses():
    init_csv()  # Make sure file exists

    # Read expenses from CSV
    expense_list = []
    try:
        with open(EXPENSES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            expense_list = list(reader)
    except Exception as e:
        print(f"Error reading expenses: {e}")

    return render_template('expenses.html', expenses=expense_list)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    init_csv()  # Make sure file exists

    try:
        # Get form data
        amount = request.form.get('amount')
        description = request.form.get('description')
        category = request.form.get('category')
        date = datetime.now().strftime('%Y-%m-%d')

        # Save to CSV
        with open(EXPENSES_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date, amount, description, category])

        print(f"Added expense: {description} - ${amount}")
    except Exception as e:
        print(f"Error adding expense: {e}")

    # Redirect back to expenses page
    return redirect('/expenses')

@app.route('/income')
def income():
    return render_template('income.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)