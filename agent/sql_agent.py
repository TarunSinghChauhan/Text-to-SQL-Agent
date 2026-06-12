from typing import Annotated, List, Dict, Any, TypedDict, Union
import operator
import pandas as pd
import psycopg2
import sqlglot
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
import os
import json

# Import our RAG system
import sys
# Add parent and rag directory to path so we can import RAG
sys.path.append("C:/Users/Tarun/.gemini/antigravity/scratch/sql_agent_project")
from rag.rag_pipeline import SchemaRAG, TableSelector, BusinessGlossaryRAG, SimilarQueriesRAG

class AgentState(TypedDict):
    query: str
    intent: str
    selected_tables: List[Dict[str, Any]]
    glossary_context: str
    few_shot_examples: str
    generated_sql: str
    validation_results: Dict[str, Any]
    execution_results: Union[pd.DataFrame, str]
    explanation: str
    error_message: str
    attempts: int
    logs: List[str]

class SQLAgent:
    def __init__(self, db_config: Dict[str, str], model_name: str = "claude-3-5-sonnet-20240620"):
        self.db_config = db_config
        self.llm = ChatAnthropic(model=model_name, temperature=0)
        
        # Initialize RAG components
        self.schema_rag = SchemaRAG()
        self.table_selector = TableSelector(self.schema_rag)
        self.glossary_rag = BusinessGlossaryRAG()
        self.similar_queries_rag = SimilarQueriesRAG()
        
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        builder = StateGraph(AgentState)
        
        # Define nodes
        builder.add_node("classify", self.classify_query_intent)
        builder.add_node("retrieve_context", self.retrieve_context)
        builder.add_node("generate", self.generate_sql)
        builder.add_node("validate", self.validate_sql)
        builder.add_node("execute", self.execute_sql)
        builder.add_node("explain", self.explain_results)
        builder.add_node("correct", self.self_correct)
        
        # Set entry point
        builder.set_entry_point("classify")
        
        # Define edges
        builder.add_edge("classify", "retrieve_context")
        builder.add_edge("retrieve_context", "generate")
        builder.add_edge("generate", "validate")
        
        builder.add_conditional_edges(
            "validate",
            lambda x: "execute" if x["validation_results"]["is_valid"] else "correct",
            {"execute": "execute", "correct": "correct"}
        )
        
        builder.add_conditional_edges(
            "execute",
            lambda x: "explain" if not x["error_message"] else "correct",
            {"explain": "explain", "correct": "correct"}
        )
        
        builder.add_conditional_edges(
            "correct",
            lambda x: "validate" if x["attempts"] < 3 else "explain",
            {"validate": "validate", "explain": "explain"}
        )
        
        builder.add_edge("explain", END)
        
        return builder.compile()

    # --- Tool 1: Classify Query Intent ---
    def classify_query_intent(self, state: AgentState):
        query = state["query"]
        prompt = ChatPromptTemplate.from_template("""
        Classify the following user business question into one of these intents:
        - simple_aggregation: Single table, basic COUNT, SUM, AVG.
        - multi_table_join: Requires joining 2+ tables.
        - time_series_analysis: Analyzing trends over time (MoM, YoY).
        - ranking_query: Top N, Bottom N, RANK() functions.
        - subquery_required: Complex logic requiring CTEs or subqueries.
        - ambiguous: Question is unclear.
        
        Question: {query}
        
        Return JSON format: {{"intent": "...", "reasoning": "..."}}
        """)
        chain = prompt | self.llm | (lambda x: json.loads(x.content))
        result = chain.invoke({"query": query})
        return {**state, "intent": result["intent"], "attempts": 0, "logs": [f"Intent classified as {result['intent']}"]}

    # --- Tool 2: Select Tables & Retrieve Context ---
    def retrieve_context(self, state: AgentState):
        query = state["query"]
        intent = state["intent"]
        
        # 1. Select relevant tables
        selected_tables = self.table_selector.select_relevant_tables(query)
        
        # 2. Get business definitions
        glossary = self.glossary_rag.retrieve_definitions(query)
        
        # 3. Get similar queries
        examples = self.similar_queries_rag.retrieve_similar_queries(query)
        
        return {
            **state, 
            "selected_tables": selected_tables, 
            "glossary_context": glossary, 
            "few_shot_examples": examples,
            "logs": state["logs"] + [f"Retrieved {len(selected_tables)} relevant tables and glossary context."]
        }

    # --- Tool 3: Generate SQL ---
    def generate_sql(self, state: AgentState):
        schema_context = ""
        for table in state["selected_tables"]:
            schema_context += f"Table: {table['schema_name']}.{table['table_name']}\n"
            for col in table['columns']:
                schema_context += f"  - {col['column_name']} ({col['data_type']}): {col['description']}\n"
        
        prompt = ChatPromptTemplate.from_template("""
        You are an expert Data Engineer. Generate a PostgreSQL SQL query to answer the user question.
        
        Rules:
        - ALWAYS use schema-qualified table names (e.g., ecommerce.orders).
        - NEVER use SELECT *. Specify columns.
        - Use CTEs (WITH clause) for complex logic.
        - Add a LIMIT 1000 unless it's an aggregation.
        - Add comments -- explaining each step.
        - Use these business definitions if relevant: {glossary}
        
        User Question: {query}
        Intent: {intent}
        
        Schema Context:
        {schema}
        
        Similar Past Queries for Reference:
        {examples}
        
        Return ONLY the SQL code block.
        """)
        
        response = self.llm.invoke(prompt.format(
            query=state["query"],
            intent=state["intent"],
            schema=schema_context,
            glossary=state["glossary_context"],
            examples=state["few_shot_examples"]
        ))
        
        sql = response.content.strip().replace("```sql", "").replace("```", "")
        return {**state, "generated_sql": sql, "logs": state["logs"] + ["Generated SQL query."]}

    # --- Tool 4: Validate SQL (using sqlglot) ---
    def validate_sql(self, state: AgentState):
        sql = state["generated_sql"]
        try:
            parsed = sqlglot.parse_one(sql, read="postgres")
            # Check for cartesian products or common anti-patterns
            is_valid = True
            error = None
            
            # Simple check for JOIN without ON (simplified)
            if " JOIN " in sql.upper() and " ON " not in sql.upper() and " USING " not in sql.upper():
                is_valid = False
                error = "Possible cartesian product detected: JOIN without ON condition."
                
        except Exception as e:
            is_valid = False
            error = str(e)
            
        return {
            **state, 
            "validation_results": {"is_valid": is_valid, "error": error},
            "logs": state["logs"] + [f"Validation {'passed' if is_valid else 'failed'}: {error if error else ''}"]
        }

    # --- Tool 5: Execute SQL ---
    def execute_sql(self, state: AgentState):
        sql = state["generated_sql"]
        try:
            conn = psycopg2.connect(**self.db_config)
            df = pd.read_sql_query(sql, conn)
            conn.close()
            return {
                **state, 
                "execution_results": df, 
                "error_message": "",
                "logs": state["logs"] + [f"Executed SQL successfully. Returned {len(df)} rows."]
            }
        except Exception as e:
            return {
                **state, 
                "error_message": str(e),
                "logs": state["logs"] + [f"Execution error: {str(e)}"]
            }

    # --- Tool 6: Explain Results ---
    def explain_results(self, state: AgentState):
        if state.get("error_message") and state["attempts"] >= 3:
            explanation = f"Failed to execute query after 3 attempts. Error: {state['error_message']}"
        else:
            df = state["execution_results"]
            prompt = ChatPromptTemplate.from_template("""
            You are a Senior Business Analyst. Explain the following SQL query results to the user in natural language.
            
            Question: {query}
            SQL Used: {sql}
            Results (First 10 rows):
            {results}
            
            Requirements:
            - Summarize the key findings.
            - Format numbers nicely (currency $, K/M suffixes).
            - Provide 2-3 key insights.
            - Suggest 2-3 follow-up questions.
            """)
            
            explanation = self.llm.invoke(prompt.format(
                query=state["query"],
                sql=state["generated_sql"],
                results=df.head(10).to_string() if isinstance(df, pd.DataFrame) else "No results"
            )).content
            
        return {**state, "explanation": explanation, "logs": state["logs"] + ["Generated explanation."]}

    # --- Tool 7: Self-Correct ---
    def self_correct(self, state: AgentState):
        error = state["validation_results"]["error"] or state["error_message"]
        failed_sql = state["generated_sql"]
        attempts = state["attempts"] + 1
        
        prompt = ChatPromptTemplate.from_template("""
        The following SQL query failed.
        
        Failed SQL:
        {sql}
        
        Error Message:
        {error}
        
        Reason about why it failed and provide a corrected PostgreSQL SQL query.
        Return ONLY the corrected SQL code block.
        """)
        
        corrected_sql = self.llm.invoke(prompt.format(sql=failed_sql, error=error)).content.strip().replace("```sql", "").replace("```", "")
        
        return {
            **state, 
            "generated_sql": corrected_sql, 
            "attempts": attempts,
            "logs": state["logs"] + [f"Self-correction attempt {attempts}."]
        }

    def run(self, query: str):
        initial_state = {
            "query": query,
            "intent": "",
            "selected_tables": [],
            "glossary_context": "",
            "few_shot_examples": "",
            "generated_sql": "",
            "validation_results": {},
            "execution_results": None,
            "explanation": "",
            "error_message": "",
            "attempts": 0,
            "logs": []
        }
        return self.workflow.invoke(initial_state)

# Configuration for testing (Update with your Postgres credentials)
DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

if __name__ == "__main__":
    agent = SQLAgent(DB_CONFIG)
    # response = agent.run("What is the total revenue for Pro customers in 2024?")
    # print(response["explanation"])
