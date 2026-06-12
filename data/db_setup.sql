-- COMPLETE DATABASE SETUP SCRIPT FOR TEXT-TO-SQL AGENT
CREATE SCHEMA IF NOT EXISTS ecommerce;
CREATE SCHEMA IF NOT EXISTS finance;
CREATE SCHEMA IF NOT EXISTS hr;

CREATE TABLE ecommerce.customers (
  customer_id INT,
  name VARCHAR(255),
  email VARCHAR(255),
  country VARCHAR(255),
  signup_date DATE,
  plan_tier VARCHAR(255),
  ltv_score NUMERIC(15, 2),
  acquisition_channel VARCHAR(255)
);
CREATE INDEX idx_customers_customer_id ON ecommerce.customers(customer_id);

CREATE TABLE ecommerce.products (
  product_id INT,
  name VARCHAR(255),
  category VARCHAR(255),
  subcategory VARCHAR(255),
  brand VARCHAR(255),
  cost_price NUMERIC(15, 2),
  selling_price NUMERIC(15, 2),
  stock_quantity INT,
  supplier_id INT
);
CREATE INDEX idx_products_product_id ON ecommerce.products(product_id);

CREATE TABLE ecommerce.orders (
  order_id INT,
  customer_id INT,
  product_id INT,
  order_date DATE,
  quantity INT,
  status VARCHAR(255),
  shipping_country VARCHAR(255),
  unit_price NUMERIC(15, 2),
  total_amount NUMERIC(15, 2)
);
CREATE INDEX idx_orders_customer_id ON ecommerce.orders(customer_id);
CREATE INDEX idx_orders_product_id ON ecommerce.orders(product_id);
CREATE INDEX idx_orders_order_date ON ecommerce.orders(order_date);

CREATE TABLE ecommerce.returns (
  return_id INT,
  order_id INT,
  return_date DATE,
  reason VARCHAR(255),
  status VARCHAR(255),
  refund_amount NUMERIC(15, 2)
);

CREATE TABLE finance.transactions (
  transaction_id INT,
  account_id INT,
  transaction_date DATE,
  amount NUMERIC(15, 2),
  transaction_type VARCHAR(255),
  category VARCHAR(255),
  merchant_name VARCHAR(255),
  currency VARCHAR(255)
);
CREATE INDEX idx_transactions_account_id ON finance.transactions(account_id);
CREATE INDEX idx_transactions_transaction_date ON finance.transactions(transaction_date);

CREATE TABLE finance.accounts (
  account_id INT,
  customer_id INT,
  account_type VARCHAR(255),
  balance NUMERIC(15, 2),
  opened_date DATE,
  status VARCHAR(255)
);
CREATE INDEX idx_accounts_account_id ON finance.accounts(account_id);
CREATE INDEX idx_accounts_customer_id ON finance.accounts(customer_id);

CREATE TABLE finance.budget (
  department VARCHAR(255),
  category VARCHAR(255),
  allocated_amount NUMERIC(15, 2),
  spent_amount NUMERIC(15, 2),
  fiscal_year INT,
  quarter INT
);

CREATE TABLE hr.employees (
  employee_id INT,
  name VARCHAR(255),
  department VARCHAR(255),
  role VARCHAR(255),
  salary NUMERIC(15, 2),
  hire_date DATE,
  manager_id INT,
  performance_score INT,
  location VARCHAR(255)
);
CREATE INDEX idx_employees_employee_id ON hr.employees(employee_id);

CREATE TABLE hr.attendance (
  employee_id INT,
  date DATE,
  check_in VARCHAR(255),
  check_out VARCHAR(255),
  hours_worked NUMERIC(15, 2),
  leave_type VARCHAR(255)
);
CREATE INDEX idx_attendance_employee_id ON hr.attendance(employee_id);

CREATE TABLE hr.payroll (
  employee_id INT,
  pay_period VARCHAR(255),
  base_salary NUMERIC(15, 2),
  bonus NUMERIC(15, 2),
  deductions NUMERIC(15, 2),
  net_pay NUMERIC(15, 2)
);
CREATE INDEX idx_payroll_employee_id ON hr.payroll(employee_id);

-- To populate data, use the COPY command in PostgreSQL:
-- COPY ecommerce.customers FROM '/path/to/data/ecommerce_customers.csv' WITH (FORMAT csv, HEADER true);
-- COPY ecommerce.products FROM '/path/to/data/ecommerce_products.csv' WITH (FORMAT csv, HEADER true);
-- COPY ecommerce.orders FROM '/path/to/data/ecommerce_orders.csv' WITH (FORMAT csv, HEADER true);
-- COPY ecommerce.returns FROM '/path/to/data/ecommerce_returns.csv' WITH (FORMAT csv, HEADER true);
-- COPY finance.transactions FROM '/path/to/data/finance_transactions.csv' WITH (FORMAT csv, HEADER true);
-- COPY finance.accounts FROM '/path/to/data/finance_accounts.csv' WITH (FORMAT csv, HEADER true);
-- COPY finance.budget FROM '/path/to/data/finance_budget.csv' WITH (FORMAT csv, HEADER true);
-- COPY hr.employees FROM '/path/to/data/hr_employees.csv' WITH (FORMAT csv, HEADER true);
-- COPY hr.attendance FROM '/path/to/data/hr_attendance.csv' WITH (FORMAT csv, HEADER true);
-- COPY hr.payroll FROM '/path/to/data/hr_payroll.csv' WITH (FORMAT csv, HEADER true);
