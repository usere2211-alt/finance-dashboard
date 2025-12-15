from flask import Flask, render_template, request, redirect
import csv
import os
from datetime import datetime

app = Flask(__name__)

# CSV file to store expenses
EXPENSES_FILE = 'expenses.csv'

# Create CSV file if it doesn't exist
if not os.path.exists(EXPENSES_FILE):
    with open(EXPENSES_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'amount', 'description', 'category'])

@app.route("/")
def home():
    return render_template('home.html')

@app.route('/expenses')
def expenses():
    # Read expenses from CSV
    expense_list = []
    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            expense_list = list(reader)

    return render_template('expenses.html', expenses=expense_list)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    # Get form data
    amount = request.form['amount']
    description = request.form['description']
    category = request.form['category']
    date = datetime.now().strftime('%Y-%m-%d')

    # Save to CSV
    with open(EXPENSES_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([date, amount, description, category])

    # Redirect back to expenses page
    return redirect('/expenses')

@app.route('/income')
def income():
    return render_template('income.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)