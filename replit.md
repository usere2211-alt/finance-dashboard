# Finance Dashboard

## Overview

A personal finance management web application built with Flask that allows users to track expenses, income, and budgets. The application provides a dashboard with visualizations, category-based spending analysis, and financial predictions using machine learning.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask** serves as the web framework, handling routing and template rendering
- Python-based backend with straightforward file-based data storage
- Server-side rendering using Jinja2 templates

### Data Storage
- **CSV files** are used for persistent storage instead of a traditional database
  - `expenses.csv` - Stores expense records with amount, category, date
  - `income.csv` - Stores income records
  - `budgets.csv` - Stores budget limits per category
- Files are initialized with headers if they don't exist
- Simple read/write operations for CRUD functionality

### Frontend Architecture
- Server-rendered HTML templates in the `/templates` directory
- Inline CSS styling with a consistent purple/gradient design theme
- Chart.js library for data visualizations on the dashboard
- Google Fonts (Inter) for typography

### Key Features
- Expense tracking with category classification
- Income tracking
- Budget management per category
- Dashboard with financial summaries and charts
- Date-based filtering
- Expense prediction using linear regression (scikit-learn)
- CSV export functionality

### Machine Learning Integration
- **scikit-learn's LinearRegression** is used for expense forecasting
- Predictions are based on historical spending patterns

## External Dependencies

### Python Libraries
- **Flask** - Web framework for routing and templating
- **scikit-learn** - Machine learning library for expense predictions
- **NumPy** - Numerical computing support for ML operations

### Frontend CDN Resources
- **Chart.js** - JavaScript charting library for dashboard visualizations
- **Google Fonts** - Inter font family for UI typography

### File System
- Application reads/writes directly to CSV files in the project root directory
- No external database connection required