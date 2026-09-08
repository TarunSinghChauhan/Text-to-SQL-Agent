from data.generate_data import save_and_generate_sql

import pytest
import pandas as pd
import os
from data.generate_data import save_and_generate_sql

def test_save_and_generate_sql_branching(tmp_path, monkeypatch):
    # Setup mocking
    monkeypatch.setattr("data.generate_data.DATA_DIR", tmp_path)
    
    # Test data covering all branches (int, float, date, string, indexing)
    df = pd.DataFrame({
        'customer_id': [1],  # Hits index column
        'val_int': [10],
        'val_float': [10.5],
        'start_date': pd.to_datetime(['2023-01-01']),
        'name': ['test']
    })
    dfs = {'ecommerce.test_table': df}
    
    save_and_generate_sql(dfs)
    
    sql_path = tmp_path / "db_setup.sql"
    assert sql_path.exists()
    
    content = sql_path.read_text()
    assert "INT" in content
    assert "NUMERIC(15, 2)" in content
    assert "DATE" in content
    assert "VARCHAR(255)" in content
    assert "CREATE INDEX idx_test_table_customer_id" in content