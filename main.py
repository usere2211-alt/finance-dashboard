import csv
import os
from datetime import datetime
import io
from flask import Flask, redirect, render_template, request, send_file
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import datetime, timedelta  # Add timedelta here!

app = Flask(__name__)

# CSV files
EXPENSES_FILE = 'expenses.csv'
INCOME_FILE = 'income.csv'
BUDGETS_FILE = 'budgets.csv'


def init_csv(filename, headers):
    """Create CSV file if it doesn't exist"""
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

def calculate_total(filename):
    """Calculate total amount from CSV file"""
    total = 0
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total += float(row['amount'])
        except:
            pass
    return total

def get_top_category(filename):
    """Find the category with highest spending"""
    category_totals = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    category = row['category']
                    amount = float(row['amount'])
                    if category in category_totals:
                        category_totals[category] += amount
                    else:
                        category_totals[category] = amount
        except:
            pass

    if category_totals:
        top_category = max(category_totals, key=lambda x: category_totals[x])
        return top_category, category_totals[top_category]
    return None, 0

@app.route("/")
def home():
    # Get filter parameters
    filter_type = request.args.get('filter', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Calculate date ranges based on filter type
    today = datetime.now()

    if filter_type == 'this_month':
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif filter_type == 'last_month':
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        start_date = first_day_last_month.strftime('%Y-%m-%d')
        end_date = last_day_last_month.strftime('%Y-%m-%d')
    elif filter_type == 'last_3_months':
        start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    # If filter_type == 'all' or custom dates, use start_date/end_date from form

    # Apply date filter to expenses
    if filter_type == 'all' and not start_date and not end_date:
        filtered_expenses = get_expenses()
    else:
        filtered_expenses = filter_expenses_by_date(start_date, end_date)

    # Calculate stats from filtered expenses
    total_expenses = sum(float(e['amount']) for e in filtered_expenses)
    total_income = calculate_total(INCOME_FILE)  # TODO: Add income filtering later
    balance = total_income - total_expenses

    # Get category breakdown from filtered expenses
    category_breakdown = {}
    for expense in filtered_expenses:
        category = expense['category']
        amount = float(expense['amount'])
        if category in category_breakdown:
            category_breakdown[category] += amount
        else:
            category_breakdown[category] = amount

    # Get top category
    top_category = None
    top_amount = 0
    if category_breakdown:
        top_category = max(category_breakdown, key=category_breakdown.get)
        top_amount = category_breakdown[top_category]

    # ML Predictions (still use all data for predictions)
    budget_status = get_budget_status()
    ml_prediction = predict_next_month_ml()
    simple_prediction = predict_next_month_spending()
    monthly_data = get_monthly_spending()

    stats = {
        'total_expenses': total_expenses,
        'total_income': total_income,
        'balance': balance,
        'top_category': top_category,
        'top_amount': top_amount,
        'category_breakdown': category_breakdown,
        'budget_status': budget_status,
        'ml_prediction': ml_prediction,
        'simple_prediction': simple_prediction,
        'num_months': len(monthly_data)
    }

    return render_template('home.html', stats=stats)
    
@app.route('/expenses')
def expenses():
    init_csv(EXPENSES_FILE, ['date', 'amount', 'description', 'category'])

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
    init_csv(EXPENSES_FILE, ['date', 'amount', 'description', 'category'])

    try:
        amount_str = request.form.get('amount')
        description = request.form.get('description')
        category = request.form.get('category')

        # ✅ Validate amount is a valid number
        try:
            amount = float(amount_str)
            if amount <= 0:
                print("Error: Amount must be positive")
                return redirect('/expenses')
        except (ValueError, TypeError):
            print(f"Error: Invalid amount '{amount_str}'")
            return redirect('/expenses')

        date = datetime.now().strftime('%Y-%m-%d')

        with open(EXPENSES_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date, amount, description, category])

        print(f"Added expense: {description} - ${amount}")
    except Exception as e:
        print(f"Error adding expense: {e}")

    return redirect('/expenses')

@app.route('/delete_expense/<int:index>')
def delete_expense(index):
    """Delete an expense at the given index"""

    expenses = []
    try:
        with open(EXPENSES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            expenses = list(reader)

        if 0 <= index < len(expenses):
            del expenses[index]

        with open(EXPENSES_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'amount', 'description', 'category'])
            writer.writeheader()
            writer.writerows(expenses)
    except Exception as e:
        print(f"Error deleting expense: {e}")

    return redirect('/expenses')

@app.route('/income')
def income():
    init_csv(INCOME_FILE, ['date', 'amount', 'source', 'category'])

    # Read income from CSV
    income_list = []
    try:
        with open(INCOME_FILE, 'r') as f:
            reader = csv.DictReader(f)
            income_list = list(reader)
    except Exception as e:
        print(f"Error reading income: {e}")

    return render_template('income.html', incomes=income_list)

@app.route('/add_income', methods=['POST'])
def add_income():
    init_csv(INCOME_FILE, ['date', 'amount', 'source', 'category'])

    try:
        amount = request.form.get('amount')
        source = request.form.get('source')
        category = request.form.get('category')
        date = datetime.now().strftime('%Y-%m-%d')

        with open(INCOME_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date, amount, source, category])

        print(f"Added income: {source} - ${amount}")
    except Exception as e:
        print(f"Error adding income: {e}")

    return redirect('/income')

@app.route("/delete_income/<int:index>")
def delete_income(index):
    incomes = []

    try:
        with open(INCOME_FILE, "r") as f:
            reader = csv.DictReader(f)
            incomes = list(reader)

        if 0 <= index < len(incomes):
            del incomes[index]

        with open(INCOME_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'amount', 'source', 'category'])
            writer.writeheader()
            writer.writerows(incomes)
    except Exception as e:
        print(f"Error deleting income: {e}")

    return redirect('/income')

def get_category_breakdown():
    """Get spending breakdown by category"""
    category_totals = {}

    if os.path.exists(EXPENSES_FILE):
        try:
            with open(EXPENSES_FILE, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    category = row['category']
                    amount = float(row['amount'])

                    if category in category_totals:
                        category_totals[category] += amount
                    else:
                        category_totals[category] = amount
        except:
            pass

    return category_totals

@app.route('/edit_expense/<int:index>', methods=['GET', 'POST'])
def edit_expense(index):
    expenses = []

    try:
        with open(EXPENSES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            expenses = list(reader)

        if index < 0 or index >= len(expenses):
            return redirect('/expenses')

        if request.method == 'GET':
            expense = expenses[index]
            return render_template('edit_expense.html', expense=expense, index=index)

        else:  # POST
            new_amount = request.form.get('amount')
            new_description = request.form.get('description')
            new_category = request.form.get('category')

            # Update specific fields only
            expenses[index]['amount'] = new_amount
            expenses[index]['description'] = new_description
            expenses[index]['category'] = new_category

            with open(EXPENSES_FILE, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['date', 'amount', 'description', 'category'])
                writer.writeheader()
                writer.writerows(expenses)

            return redirect('/expenses')
    except Exception as e:
        print(f"Error editing expense: {e}")
        return redirect('/expenses')


def get_budgets():
    """Read budget limits from CSV"""
    budgets = {}

    if os.path.exists(BUDGETS_FILE):
        try:
            with open(BUDGETS_FILE, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    category = row['category']
                    budget = float(row['budget'])
                    budgets[category] = budget
        except Exception as e:
            print(f"Error reading budgets: {e}")

    return budgets

def get_expenses():
    """Get all expenses as list of dictionaries"""
    expenses = []
    if os.path.exists(EXPENSES_FILE):
        try:
            with open(EXPENSES_FILE, 'r') as f:
                reader = csv.DictReader(f)
                expenses = list(reader)
        except Exception as e:
            print(f"Error reading expenses: {e}")
    return expenses


def get_income():
    """Get all income as list of dictionaries"""
    incomes = []
    if os.path.exists(INCOME_FILE):
        try:
            with open(INCOME_FILE, 'r') as f:
                reader = csv.DictReader(f)
                incomes = list(reader)
        except Exception as e:
            print(f"Error reading income: {e}")
    return incomes

def get_monthly_spending():
    """
    Calculate total spending per month
    Returns: dictionary like {'2024-12': 500.0, '2024-11': 450.0}
    """
    monthly_totals = {}

    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = row['date']
                month = date[:7]
                amount = float(row['amount'])

                if month in monthly_totals:
                    monthly_totals[month] += amount
                else:
                    monthly_totals[month] = amount

    return monthly_totals

def filter_expenses_by_date(start_date=None, end_date=None):
    """
    Filter expenses by date range
    """
    expenses = get_expenses()

    if not start_date and not end_date:
        return expenses

    filtered = []
    for expense in expenses:
        expense_date = expense['date']

        # Case 1: Both dates provided
        if start_date and end_date:
            if expense_date >= start_date and expense_date <= end_date:
                filtered.append(expense)  # Fix this

        # Case 2: Only start_date provided (show all AFTER this date)
        elif start_date:
            if expense_date >= start_date:
                filtered.append(expense)  # Add this

        # Case 3: Only end_date provided (show all BEFORE this date)
        elif end_date:
            if expense_date <= end_date:
                filtered.append(expense)  # Add this

    return filtered

def predict_next_month_spending():
    """
    Predict next month's spending based on historical average
    Returns: predicted amount (float)
    """
    monthly_data = get_monthly_spending()

    if not monthly_data:
        return 0

    total = sum(monthly_data.values())  # ✅ Fixed!
    num_months = len(monthly_data)      # ✅ Perfect!
    average = total / num_months         # ✅ Perfect!

    return average

def predict_next_month_ml():
    """
    Use Linear Regression to predict next month's spending
    Returns: predicted amount (float)
    """
    monthly_data = get_monthly_spending()

    # Need at least 2 months for ML
    if len(monthly_data) < 2:
        # Fallback to simple average
        return predict_next_month_spending()

    # Prepare data for ML
    months = sorted(monthly_data.keys())

    # X = month numbers (0, 1, 2, ...)
    X = []
    for i in range(len(months)):
        X.append([i])

    # y = spending amounts
    y = []
    for month in months:
        y.append(monthly_data[month])

    # Create and train the model
    model = LinearRegression()
    model.fit(X, y)

    # Predict next month
    next_month_number = [[len(months)]]
    prediction = model.predict(next_month_number)

    return prediction[0]


@app.route('/test_prediction')
def test_prediction():
    prediction = predict_next_month_spending()
    return f"Predicted next month spending: ${prediction:.2f}"

@app.route('/test_monthly')  # ✅ Test route right after
def test_monthly():
    monthly = get_monthly_spending()
    return str(monthly)
    
def save_budgets(budgets):
    """Save budget limits to CSV"""
    try:
        with open(BUDGETS_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['category', 'budget'])
            writer.writeheader()

            for category, budget in budgets.items():
                writer.writerow({'category': category, 'budget': budget})
    except Exception as e:
        print(f"Error saving budgets: {e}")


def get_budget_status():
    """Calculate spending vs budget for each category"""
    budgets = get_budgets()
    spending = get_category_breakdown()

    status = {}
    for category in budgets:
        budget_limit = budgets[category]
        spent = spending.get(category, 0)

        percentage = (spent / budget_limit * 100) if budget_limit > 0 else 0
        is_over = spent > budget_limit

        if percentage < 70:
            color = 'green'
        elif percentage < 100:
            color = 'yellow'
        else:
            color = 'red'

        status[category] = {
            'budget': budget_limit,
            'spent': spent,
            'remaining': budget_limit - spent,
            'percentage': percentage,
            'color': color,
            'is_over': is_over
        }

    return status

@app.route('/budgets')
def budgets():
    budget_status = get_budget_status()
    return render_template('budgets.html', budget_status=budget_status)


@app.route('/set_budget', methods=['POST'])
def set_budget():
    try:
        budgets = get_budgets()

        category = request.form.get('category')
        budget = float(request.form.get('budget'))

        budgets[category] = budget
        save_budgets(budgets)

        print(f"Set budget: {category} = ${budget}")
    except Exception as e:
        print(f"Error setting budget: {e}")

    return redirect('/budgets')


@app.route('/delete_budget/<category>')
def delete_budget(category):
    try:
        budgets = get_budgets()
        if category in budgets:
            del budgets[category]
            save_budgets(budgets)
    except Exception as e:
        print(f"Error deleting budget: {e}")

    return redirect('/budgets')

@app.route('/export/expenses')
def export_expenses():
    """Export expenses as CSV"""
    expenses = get_expenses()

    output = io.StringIO()
    if expenses:
        headers = expenses[0].keys()
        output.write(','.join(headers) + '\n')

        for expense in expenses:
            row = ','.join(str(expense[h]) for h in headers)
            output.write(row + '\n')

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='expenses.csv'
    )


@app.route('/export/income')
def export_income():
    """Export income as CSV"""
    incomes = get_income()

    output = io.StringIO()
    if incomes:
        headers = incomes[0].keys()
        output.write(','.join(headers) + '\n')

        for income in incomes:
            row = ','.join(str(income[h]) for h in headers)
            output.write(row + '\n')

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='income.csv'
    )


@app.route('/export/all')
def export_all():
    """Export combined financial summary"""
    expenses = get_expenses()
    incomes = get_income()

    output = io.StringIO()

    output.write('=== EXPENSES ===\n')
    if expenses:
        headers = expenses[0].keys()
        output.write(','.join(headers) + '\n')
        for expense in expenses:
            row = ','.join(str(expense[h]) for h in headers)
            output.write(row + '\n')

    output.write('\n=== INCOME ===\n')
    if incomes:
        headers = incomes[0].keys()
        output.write(','.join(headers) + '\n')
        for income in incomes:
            row = ','.join(str(income[h]) for h in headers)
            output.write(row + '\n')

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='financial_report.csv'
    )

@app.route('/test_ml')
def test_ml():
    monthly_data = get_monthly_spending()
    num_months = len(monthly_data)

    prediction = predict_next_month_ml()
    simple = predict_next_month_spending()

    return f"""
    <h2>💡 Prediction Comparison:</h2>
    <p><strong>Months of Data:</strong> {num_months}</p>
    <p><strong>Simple Average:</strong> ${simple:.2f}</p>
    <p><strong>ML Prediction (Linear Regression):</strong> ${prediction:.2f}</p>
    <p><strong>Difference:</strong> ${abs(prediction - simple):.2f}</p>
    <hr>
    <p><em>The ML model detects trends - if spending is increasing, it predicts higher than average!</em></p>
    """

@app.route('/test_filter')
def test_filter():
    # Test 1: All expenses
    all_expenses = filter_expenses_by_date()

    # Test 2: Only December 2025
    december = filter_expenses_by_date('2025-12-01', '2025-12-31')

    # Test 3: From November onwards
    from_nov = filter_expenses_by_date('2025-11-01', None)

    return f"""
    <h2>Date Filter Test:</h2>
    <p><strong>All Expenses:</strong> {len(all_expenses)} items</p>
    <p><strong>December Only:</strong> {len(december)} items</p>
    <p><strong>From November:</strong> {len(from_nov)} items</p>
    <hr>
    <h3>December Expenses:</h3>
    <ul>
    {''.join(f"<li>{e['date']} - {e['description']} - ${e['amount']}</li>" for e in december)}
    </ul>
    """


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)