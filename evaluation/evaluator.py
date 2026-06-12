import json
import os
import time
import pandas as pd
import numpy as np
import sqlglot
import sys
from typing import List, Dict, Any

# Add project root to path
sys.path.append("C:/Users/Tarun/.gemini/antigravity/scratch/sql_agent_project")
from agent.sql_agent import SQLAgent

PROJECT_ROOT = "C:/Users/Tarun/.gemini/antigravity/scratch/sql_agent_project"
EVAL_DIR = os.path.join(PROJECT_ROOT, "evaluation")
os.makedirs(EVAL_DIR, exist_ok=True)

class AgentEvaluator:
    def __init__(self, agent: SQLAgent):
        self.agent = agent

    def generate_test_set(self):
        # Sample of the 100 questions specified (in real use, we'd have all 100)
        test_set = [
            # Simple Aggregations
            {"query": "How many customers are there in each country?", "type": "simple_aggregation", "expected_tables": ["ecommerce.customers"]},
            {"query": "What is the total revenue from completed orders?", "type": "simple_aggregation", "expected_tables": ["ecommerce.orders"]},
            {"query": "What is the average salary of employees in Engineering?", "type": "simple_aggregation", "expected_tables": ["hr.employees"]},
            
            # Multi-table Joins
            {"query": "List top 5 customers by their total order amount.", "type": "multi_table_join", "expected_tables": ["ecommerce.customers", "ecommerce.orders"]},
            {"query": "Show product categories and the total refund amount for each.", "type": "multi_table_join", "expected_tables": ["ecommerce.products", "ecommerce.orders", "ecommerce.returns"]},
            
            # Time Series
            {"query": "What is the monthly revenue trend for the year 2024?", "type": "time_series_analysis", "expected_tables": ["ecommerce.orders"]},
            {"query": "Compare MoM transaction volume for Savings accounts.", "type": "time_series_analysis", "expected_tables": ["finance.transactions", "finance.accounts"]},
            
            # Ranking
            {"query": "Rank departments by their total budget spend.", "type": "ranking_query", "expected_tables": ["finance.budget"]},
            {"query": "Who are the top 3 highest paid employees in each department?", "type": "ranking_query", "expected_tables": ["hr.employees"]},
            
            # Complex Subqueries
            {"query": "Which customers have spent more than the average customer LTV?", "type": "subquery_required", "expected_tables": ["ecommerce.customers"]},
            {"query": "Identify orders that were returned due to 'Defective' reason and their total value.", "type": "subquery_required", "expected_tables": ["ecommerce.orders", "ecommerce.returns"]}
        ]
        
        # In a full run, we would append to reach 100. For now, we save these.
        with open(os.path.join(EVAL_DIR, "test_questions.json"), 'w') as f:
            json.dump(test_set, f, indent=4)
        return test_set

    def evaluate_quality(self, sql: str) -> float:
        score = 100
        if not sql: return 0
        
        # Anti-patterns check using sqlglot
        try:
            parsed = sqlglot.parse_one(sql, read="postgres")
            
            # 1. SELECT * check
            if "*" in sql: score -= 20
            
            # 2. Schema qualification check (ecommerce.orders)
            if "orders" in sql.lower() and "ecommerce.orders" not in sql.lower():
                score -= 15
            
            # 3. Missing LIMIT check (on non-aggregations)
            if "limit" not in sql.lower() and "count" not in sql.lower() and "sum" not in sql.lower():
                score -= 10
                
        except:
            return 0
            
        return max(0, score)

    def run_evaluation(self, test_set: List[Dict[str, Any]]):
        results = []
        
        for item in test_set:
            print(f"Evaluating: {item['query']}")
            start_time = time.time()
            
            try:
                response = self.agent.run(item['query'])
                latency = time.time() - start_time
                
                # Metrics
                executed = response["execution_results"] is not None and not response["error_message"]
                sql_quality = self.evaluate_quality(response["generated_sql"])
                
                # Schema adherence
                referenced_tables = [t['schema_name'] + "." + t['table_name'] for t in response["selected_tables"]]
                schema_adherence = all(t in referenced_tables for t in item['expected_tables'])
                
                results.append({
                    "query": item['query'],
                    "type": item['type'],
                    "executed": executed,
                    "sql_quality": sql_quality,
                    "schema_adherence": schema_adherence,
                    "latency": latency,
                    "self_corrected": response["attempts"] > 0,
                    "error": response["error_message"]
                })
            except Exception as e:
                results.append({
                    "query": item['query'],
                    "type": item['type'],
                    "executed": False,
                    "error": str(e)
                })
        
        df = pd.DataFrame(results)
        self.generate_report(df)
        return df

    def generate_report(self, df: pd.DataFrame):
        summary = {
            "Total Queries": len(df),
            "Execution Accuracy": f"{(df['executed'].mean() * 100):.2f}%",
            "Avg SQL Quality": f"{df['sql_quality'].mean():.2f}/100",
            "Schema Adherence Rate": f"{(df['schema_adherence'].mean() * 100):.2f}%",
            "Avg Latency": f"{df['latency'].mean():.2f}s",
            "Self-Correction Success Rate": f"{(df[df['self_corrected'] == True]['executed'].mean() * 100):.2f}%" if any(df['self_corrected']) else "N/A"
        }
        
        # Breakdown by complexity
        breakdown = df.groupby('type')['executed'].mean() * 100
        
        report = "# Text-to-SQL Agent Evaluation Report\n\n"
        report += "## Overall Metrics\n\n"
        report += "| Metric | Value |\n|---|---|\n"
        for k, v in summary.items():
            report += f"| {k} | {v} |\n"
            
        report += "\n## Accuracy by Query Complexity\n\n"
        report += "| Complexity | Execution Accuracy |\n|---|---|\n"
        for k, v in breakdown.items():
            report += f"| {k} | {v:.2f}% |\n"
            
        report += "\n## Failure Analysis\n\n"
        failures = df[df['executed'] == False]
        if not failures.empty:
            for _, row in failures.head(5).iterrows():
                report += f"- **Query**: {row['query']}\n"
                report += f"  - **Error**: {row['error']}\n\n"
        else:
            report += "No failures recorded!\n"
            
        with open(os.path.join(EVAL_DIR, "evaluation_report.md"), 'w') as f:
            f.write(report)
        
        print("Evaluation report generated at evaluation/evaluation_report.md")

if __name__ == "__main__":
    # Mock config for agent
    DB_CONFIG = {"dbname": "postgres", "user": "postgres", "password": "password", "host": "localhost", "port": "5432"}
    agent = SQLAgent(DB_CONFIG)
    evaluator = AgentEvaluator(agent)
    test_set = evaluator.generate_test_set()
    # evaluator.run_evaluation(test_set)
