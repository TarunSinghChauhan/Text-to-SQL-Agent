import pandas as pd
import numpy as np
import json
import random
from datetime import datetime, timedelta
import os

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# Using local path for the project
PROJECT_ROOT = "C:/Users/Tarun/.gemini/antigravity/scratch/sql_agent_project"
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def generate_ecommerce_data():
    print("Generating Ecommerce data...")
    
    # Customers (10,000)
    customer_ids = range(1, 10001)
    countries = ['USA', 'UK', 'Canada', 'Germany', 'France', 'India', 'Japan', 'Australia']
    channels = ['Search', 'Social Media', 'Referral', 'Email', 'Direct']
    tiers = ['Free', 'Basic', 'Pro', 'Enterprise']
    
    customers = pd.DataFrame({
        'customer_id': customer_ids,
        'name': [f"Customer_{i}" for i in customer_ids],
        'email': [f"customer_{i}@example.com" for i in customer_ids],
        'country': np.random.choice(countries, 10000),
        'signup_date': [datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365)) for _ in range(10000)],
        'plan_tier': np.random.choice(tiers, 10000, p=[0.5, 0.3, 0.15, 0.05]),
        'ltv_score': np.random.uniform(0, 5000, 10000).round(2),
        'acquisition_channel': np.random.choice(channels, 10000)
    })
    
    # Products (2,000)
    product_ids = range(1, 2001)
    categories = ['Electronics', 'Home & Kitchen', 'Fashion', 'Sports', 'Books']
    subcategories = {
        'Electronics': ['Smartphones', 'Laptops', 'Audio', 'Wearables'],
        'Home & Kitchen': ['Appliances', 'Decor', 'Cookware', 'Bedding'],
        'Fashion': ['Menswear', 'Womenswear', 'Footwear', 'Accessories'],
        'Sports': ['Fitness', 'Outdoor', 'Team Sports', 'Water Sports'],
        'Books': ['Fiction', 'Non-Fiction', 'Tech', 'Children']
    }
    
    prod_data = []
    for i in product_ids:
        cat = random.choice(categories)
        subcat = random.choice(subcategories[cat])
        cost = round(np.random.uniform(5, 500), 2)
        price = round(cost * np.random.uniform(1.2, 2.5), 2)
        prod_data.append([i, f"Product_{i}", cat, subcat, f"Brand_{random.randint(1, 50)}", cost, price, random.randint(0, 1000), random.randint(1, 100)])
    
    products = pd.DataFrame(prod_data, columns=['product_id', 'name', 'category', 'subcategory', 'brand', 'cost_price', 'selling_price', 'stock_quantity', 'supplier_id'])
    
    # Orders (50,000)
    order_ids = range(1, 50001)
    order_dates = [datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365)) for _ in range(50000)]
    
    orders = pd.DataFrame({
        'order_id': order_ids,
        'customer_id': np.random.choice(customer_ids, 50000),
        'product_id': np.random.choice(product_ids, 50000),
        'order_date': order_dates,
        'quantity': np.random.randint(1, 5, 50000),
        'status': np.random.choice(['Completed', 'Pending', 'Cancelled', 'Shipped'], 50000, p=[0.7, 0.1, 0.05, 0.15]),
        'shipping_country': np.random.choice(countries, 50000)
    })
    
    orders = orders.merge(products[['product_id', 'selling_price']], on='product_id')
    orders['unit_price'] = orders['selling_price']
    orders['total_amount'] = (orders['quantity'] * orders['unit_price']).round(2)
    orders = orders.drop(columns=['selling_price'])
    orders = orders.sort_values('order_id')
    
    # Returns (5,000)
    completed_orders = orders[orders['status'] == 'Completed']['order_id'].values
    return_ids = range(1, 5001)
    return_order_ids = np.random.choice(completed_orders, 5000, replace=False)
    
    returns = pd.DataFrame({
        'return_id': return_ids,
        'order_id': return_order_ids,
        'return_date': [orders.loc[orders['order_id'] == oid, 'order_date'].iloc[0] + timedelta(days=random.randint(1, 14)) for oid in return_order_ids],
        'reason': np.random.choice(['Defective', 'Size Issue', 'Wrong Item', 'Changed Mind'], 5000),
        'status': np.random.choice(['Processed', 'Pending', 'Rejected'], 5000, p=[0.8, 0.1, 0.1])
    })
    
    returns = returns.merge(orders[['order_id', 'total_amount']], on='order_id')
    returns['refund_amount'] = np.where(returns['status'] == 'Processed', returns['total_amount'], 0)
    returns = returns.drop(columns=['total_amount'])
    
    return customers, products, orders, returns

def generate_finance_data(customer_ids):
    print("Generating Finance data...")
    
    # Accounts
    account_ids = range(1, 10001)
    acc_types = ['Checking', 'Savings', 'Investment']
    accounts = pd.DataFrame({
        'account_id': account_ids,
        'customer_id': np.random.choice(customer_ids, 10000),
        'account_type': np.random.choice(acc_types, 10000),
        'balance': np.random.uniform(100, 50000, 10000).round(2),
        'opened_date': [datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1500)) for _ in range(10000)],
        'status': np.random.choice(['Active', 'Closed', 'Frozen'], 10000, p=[0.9, 0.05, 0.05])
    })
    
    # Transactions (100,000)
    trans_amounts = (np.random.pareto(2, 100000) + 1) * 20
    
    transactions = pd.DataFrame({
        'transaction_id': range(1, 100001),
        'account_id': np.random.choice(account_ids, 100000),
        'transaction_date': [datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365)) for _ in range(100000)],
        'amount': trans_amounts.round(2),
        'transaction_type': np.random.choice(['Debit', 'Credit'], 100000),
        'category': np.random.choice(['Groceries', 'Rent', 'Utilities', 'Entertainment', 'Salary', 'Transfer', 'Shopping'], 100000),
        'merchant_name': [f"Merchant_{random.randint(1, 500)}" for _ in range(100000)],
        'currency': 'USD'
    })
    
    # Budget
    depts = ['Sales', 'Engineering', 'Marketing', 'HR', 'Operations']
    budget_cats = ['Software', 'Travel', 'Recruitment', 'Marketing Ads', 'Hardware']
    budget_data = []
    for dept in depts:
        for cat in budget_cats:
            allocated = np.random.uniform(50000, 500000)
            spent = allocated * np.random.uniform(0.7, 1.1)
            budget_data.append([dept, cat, round(allocated, 2), round(spent, 2), 2024, random.randint(1, 4)])
            
    budget = pd.DataFrame(budget_data, columns=['department', 'category', 'allocated_amount', 'spent_amount', 'fiscal_year', 'quarter'])
    
    return transactions, accounts, budget

def generate_hr_data():
    print("Generating HR data...")
    
    # Employees (500)
    depts = ['Engineering', 'Sales', 'Marketing', 'HR', 'Operations', 'Finance']
    roles = {
        'Engineering': ['SDE 1', 'SDE 2', 'Senior SDE', 'Staff Engineer', 'EM'],
        'Sales': ['Account Executive', 'SDR', 'Sales Manager'],
        'Marketing': ['Content Marketer', 'SEO Specialist', 'Marketing Manager'],
        'HR': ['Recruiter', 'HR Generalist', 'HRBP'],
        'Operations': ['Ops Analyst', 'Ops Manager'],
        'Finance': ['Accountant', 'Financial Analyst', 'Finance Manager']
    }
    
    salaries = {
        'Engineering': (100000, 20000),
        'Sales': (80000, 15000),
        'Marketing': (75000, 10000),
        'HR': (70000, 8000),
        'Operations': (70000, 12000),
        'Finance': (85000, 15000)
    }
    
    emp_data = []
    for i in range(1, 501):
        dept = random.choice(depts)
        role = random.choice(roles[dept])
        mu, sigma = salaries[dept]
        salary = round(np.random.normal(mu, sigma), 2)
        hire_date = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1500))
        perf = random.randint(1, 5)
        loc = random.choice(['NY', 'SF', 'Austin', 'Remote', 'London'])
        emp_data.append([i, f"Employee_{i}", dept, role, salary, hire_date, random.randint(1, 50), perf, loc])
        
    employees = pd.DataFrame(emp_data, columns=['employee_id', 'name', 'department', 'role', 'salary', 'hire_date', 'manager_id', 'performance_score', 'location'])
    
    # Attendance & Payroll (12 months)
    attendance_data = []
    payroll_data = []
    months = 12
    start_date = datetime(2024, 1, 1)
    
    for i in range(1, 501):
        emp_salary = employees.loc[employees['employee_id'] == i, 'salary'].iloc[0]
        monthly_base = round(emp_salary / 12, 2)
        
        for m in range(months):
            month_date = start_date + timedelta(days=m * 30)
            pay_period = month_date.strftime('%Y-%m')
            
            # Payroll
            bonus = round(monthly_base * np.random.uniform(0, 0.2), 2) if random.random() > 0.8 else 0
            deductions = round(monthly_base * 0.2, 2)
            net_pay = monthly_base + bonus - deductions
            payroll_data.append([i, pay_period, monthly_base, bonus, deductions, round(net_pay, 2)])
            
            # Attendance
            for d in range(1, 21):
                day = month_date + timedelta(days=d)
                check_in = "09:00"
                check_out = "18:00"
                hours = 8.0 + np.random.uniform(-0.5, 2.0)
                leave = None if random.random() > 0.05 else random.choice(['Sick', 'Vacation', 'Personal'])
                attendance_data.append([i, day.strftime('%Y-%m-%d'), check_in, check_out, round(hours, 2), leave])
                
    attendance = pd.DataFrame(attendance_data, columns=['employee_id', 'date', 'check_in', 'check_out', 'hours_worked', 'leave_type'])
    payroll = pd.DataFrame(payroll_data, columns=['employee_id', 'pay_period', 'base_salary', 'bonus', 'deductions', 'net_pay'])
    
    return employees, attendance, payroll

def generate_db_metadata(dfs):
    print("Generating DB metadata...")
    metadata = {}
    
    descriptions = {
        'ecommerce.customers': {
            'customer_id': 'Primary key for customer',
            'name': 'Full name of the customer',
            'email': 'Email address',
            'country': 'Country of residence',
            'signup_date': 'Date the customer joined',
            'plan_tier': 'Subscription plan: Free, Basic, Pro, Enterprise',
            'ltv_score': 'Lifetime Value score calculated by marketing',
            'acquisition_channel': 'Where the customer came from'
        },
        'ecommerce.products': {
            'product_id': 'Primary key for product',
            'name': 'Name of the product',
            'category': 'Major product category',
            'subcategory': 'Specific product subcategory',
            'brand': 'Product brand name',
            'cost_price': 'Cost to acquire the product',
            'selling_price': 'Retail price',
            'stock_quantity': 'Current inventory level',
            'supplier_id': 'Identifier for the supplier'
        },
        'ecommerce.orders': {
            'order_id': 'Primary key for order',
            'customer_id': 'Foreign key to customers',
            'product_id': 'Foreign key to products',
            'order_date': 'Date and time of order',
            'quantity': 'Number of items purchased',
            'unit_price': 'Price per unit at time of sale',
            'total_amount': 'Total order value (qty * unit_price)',
            'status': 'Order status: Completed, Pending, Cancelled, Shipped',
            'shipping_country': 'Destination country'
        },
        'ecommerce.returns': {
            'return_id': 'Primary key for return',
            'order_id': 'Foreign key to orders',
            'return_date': 'Date return was initiated',
            'reason': 'Customer reason for return',
            'refund_amount': 'Amount refunded to customer',
            'status': 'Return processing status'
        },
        'finance.transactions': {
            'transaction_id': 'Primary key for transaction',
            'account_id': 'Foreign key to accounts',
            'transaction_date': 'Date of transaction',
            'amount': 'Transaction magnitude',
            'transaction_type': 'Debit or Credit',
            'category': 'Spend or income category',
            'merchant_name': 'Vendor name',
            'currency': 'Currency code'
        },
        'finance.accounts': {
            'account_id': 'Primary key for account',
            'customer_id': 'Owner customer_id',
            'account_type': 'Checking, Savings, Investment',
            'balance': 'Current account balance',
            'opened_date': 'Account creation date',
            'status': 'Account status'
        },
        'finance.budget': {
            'department': 'Department name',
            'category': 'Budget category',
            'allocated_amount': 'Planned budget',
            'spent_amount': 'Actual spending',
            'fiscal_year': 'Year',
            'quarter': 'Quarter (1-4)'
        },
        'hr.employees': {
            'employee_id': 'Primary key for employee',
            'name': 'Full name',
            'department': 'Internal department',
            'role': 'Job title',
            'salary': 'Annual gross salary',
            'hire_date': 'Employment start date',
            'manager_id': 'Manager employee_id',
            'performance_score': 'Latest performance rating (1-5)',
            'location': 'Office location or Remote'
        },
        'hr.attendance': {
             'employee_id': 'Foreign key to employees',
             'date': 'Work date',
             'check_in': 'Arrival time',
             'check_out': 'Departure time',
             'hours_worked': 'Total hours logged',
             'leave_type': 'Type of leave if applicable'
        },
        'hr.payroll': {
             'employee_id': 'Foreign key to employees',
             'pay_period': 'Year-Month of payment',
             'base_salary': 'Base monthly pay',
             'bonus': 'Performance or other bonus',
             'deductions': 'Tax and benefit deductions',
             'net_pay': 'Final take-home pay'
        }
    }
    
    questions = {
        'ecommerce.customers': ["What is the total LTV of customers in the USA?", "How many Enterprise customers signed up in 2023?", "Which acquisition channel has the highest average LTV?"],
        'ecommerce.orders': ["What was the total revenue in Q1 2024?", "Which country had the most completed orders?", "Calculate MoM revenue growth."],
        'ecommerce.products': ["What are the top 5 most expensive products?", "List subcategories with low stock (< 10).", "Which brand has the highest average selling price?"],
        'finance.transactions': ["Show me all transactions for Merchant_12 last month.", "What is the total spend in the Groceries category?", "Identify accounts with transaction volume > $10,000."],
        'hr.employees': ["What is the average salary by department?", "Who is the longest tenured employee in Engineering?", "Show performance scores for all Sales Managers."]
    }

    for full_name, df in dfs.items():
        schema, table = full_name.split('.')
        col_meta = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            desc = descriptions.get(full_name, {}).get(col, "No description available")
            samples = df[col].head(3).tolist()
            col_meta.append({
                "column_name": col,
                "data_type": dtype,
                "description": desc,
                "sample_values": [str(s) for s in samples]
            })
        
        metadata[full_name] = {
            "table_name": table,
            "schema_name": schema,
            "columns": col_meta,
            "primary_key": df.columns[0],
            "foreign_keys": [], 
            "example_questions": questions.get(full_name, ["How many rows are in this table?", "Show me the top 5 records.", "Summarize the data by its main category."])
        }
        
    with open(os.path.join(DATA_DIR, "db_metadata.json"), 'w') as f:
        json.dump(metadata, f, indent=4)

def save_and_generate_sql(dfs):
    print("Saving CSVs and generating SQL script...")
    sql_script = []
    sql_script.append("-- COMPLETE DATABASE SETUP SCRIPT FOR TEXT-TO-SQL AGENT\n")
    sql_script.append("CREATE SCHEMA IF NOT EXISTS ecommerce;\n")
    sql_script.append("CREATE SCHEMA IF NOT EXISTS finance;\n")
    sql_script.append("CREATE SCHEMA IF NOT EXISTS hr;\n\n")
    
    for full_name, df in dfs.items():
        csv_path = os.path.join(DATA_DIR, f"{full_name.replace('.', '_')}.csv")
        df.to_csv(csv_path, index=False)
        
        schema, table = full_name.split('.')
        cols = []
        for col, dtype in zip(df.columns, df.dtypes):
            if 'int' in str(dtype):
                sql_type = "INT"
            elif 'float' in str(dtype):
                sql_type = "NUMERIC(15, 2)"
            elif 'datetime' in str(dtype) or 'date' in col:
                sql_type = "DATE"
            else:
                sql_type = "VARCHAR(255)"
            
            cols.append(f"{col} {sql_type}")
        
        create_stmt = f"CREATE TABLE {full_name} (\n  " + ",\n  ".join(cols) + "\n);\n"
        sql_script.append(create_stmt)
        
        idx_cols = ['customer_id', 'order_date', 'product_id', 'employee_id', 'transaction_date', 'account_id']
        for col in df.columns:
            if col in idx_cols:
                sql_script.append(f"CREATE INDEX idx_{table}_{col} ON {full_name}({col});\n")
        
        sql_script.append("\n")

    sql_script.append("-- To populate data, use the COPY command in PostgreSQL:\n")
    for full_name in dfs.keys():
        csv_file = f"{full_name.replace('.', '_')}.csv"
        sql_script.append(f"-- COPY {full_name} FROM '/path/to/data/{csv_file}' WITH (FORMAT csv, HEADER true);\n")

    with open(os.path.join(DATA_DIR, "db_setup.sql"), 'w') as f:
        f.writelines(sql_script)

def main():
    cust, prod, ords, ret = generate_ecommerce_data()
    trans, acc, budg = generate_finance_data(cust['customer_id'].tolist())
    emps, attn, pay = generate_hr_data()
    
    dfs = {
        'ecommerce.customers': cust,
        'ecommerce.products': prod,
        'ecommerce.orders': ords,
        'ecommerce.returns': ret,
        'finance.transactions': trans,
        'finance.accounts': acc,
        'finance.budget': budg,
        'hr.employees': emps,
        'hr.attendance': attn,
        'hr.payroll': pay
    }
    
    generate_db_metadata(dfs)
    save_and_generate_sql(dfs)
    print("Successfully generated all files in data/ directory.")

if __name__ == "__main__":
    main()
