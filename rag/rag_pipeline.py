import json
import os
from typing import List, Dict, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

PROJECT_ROOT = "C:/Users/Tarun/.gemini/antigravity/scratch/sql_agent_project"
RAG_DIR = os.path.join(PROJECT_ROOT, "rag")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(RAG_DIR, exist_ok=True)

class SchemaRAG:
    def __init__(self, persist_directory: str = os.path.join(RAG_DIR, "chroma_db")):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.persist_directory = persist_directory
        self.vectorstore = None

    def initialize_from_metadata(self, metadata_path: str):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        documents = []
        for full_table_name, details in metadata.items():
            content = f"Table: {full_table_name}\n"
            content += f"Schema: {details['schema_name']}\n"
            content += f"Description: {details.get('description', 'Business data table')}\n"
            content += "Columns:\n"
            for col in details['columns']:
                content += f" - {col['column_name']} ({col['data_type']}): {col['description']}. Sample: {', '.join(col['sample_values'])}\n"
            content += "Example Questions:\n"
            for q in details['example_questions']:
                content += f" - {q}\n"
            
            doc = Document(
                page_content=content,
                metadata={
                    "table_name": full_table_name,
                    "schema": details['schema_name'],
                    "type": "schema"
                }
            )
            documents.append(doc)
        
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        print(f"Initialized Schema RAG with {len(documents)} tables.")

    def get_relevant_tables(self, query: str, k: int = 5) -> List[Document]:
        if not self.vectorstore:
            self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
        return self.vectorstore.similarity_search(query, k=k)

class TableSelector:
    def __init__(self, schema_rag: SchemaRAG, model_name: str = "claude-3-5-sonnet-20240620"):
        self.rag = schema_rag
        self.llm = ChatAnthropic(model=model_name, temperature=0)
        self.parser = JsonOutputParser()

    def select_relevant_tables(self, user_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        docs = self.rag.get_relevant_tables(user_query, k=top_k)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        prompt = ChatPromptTemplate.from_template("""
        You are a Database Architect. Given the user's business question and the following prospective table schemas, identify EXACTLY which tables are needed to answer the question.
        Consider joins and foreign key relationships.
        
        User Question: {query}
        
        Prospective Tables:
        {context}
        
        Return a JSON object with a list of "selected_tables" and a "reasoning" for each.
        Example: {{"selected_tables": ["ecommerce.orders", "ecommerce.customers"], "reasoning": "Need orders to calculate revenue and customers to filter by country."}}
        """)
        
        chain = prompt | self.llm | self.parser
        selection = chain.invoke({"query": user_query, "context": context})
        
        # Enrich selection with full schema from metadata
        enrich_results = []
        with open(os.path.join(DATA_DIR, "db_metadata.json"), 'r') as f:
            metadata = json.load(f)
            
        for table in selection.get("selected_tables", []):
            if table in metadata:
                enrich_results.append(metadata[table])
        
        return enrich_results

class BusinessGlossaryRAG:
    def __init__(self, persist_directory: str = os.path.join(RAG_DIR, "glossary_db")):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectorstore = None
        self.persist_directory = persist_directory

    def initialize_glossary(self):
        definitions = [
            {"term": "LTV", "definition": "Lifetime Value: The total predicted revenue a customer will generate throughout their entire relationship with the company."},
            {"term": "MoM", "definition": "Month over Month: A comparison of one month's performance to the previous month's performance."},
            {"term": "Retention Rate", "definition": "The percentage of customers who continue to use the service over a given time period."},
            {"term": "AOV", "definition": "Average Order Value: The average amount spent each time a customer places an order."},
            {"term": "Churn", "definition": "The rate at which customers stop doing business with an entity."},
            {"term": "Burn Rate", "definition": "The rate at which a company spends its capital to finance overhead before generating positive cash flow from operations."}
        ]
        docs = [Document(page_content=f"{d['term']}: {d['definition']}", metadata={"term": d['term']}) for d in definitions]
        self.vectorstore = Chroma.from_documents(docs, self.embeddings, persist_directory=self.persist_directory)

    def retrieve_definitions(self, query: str, k: int = 2) -> str:
        if not self.vectorstore:
            self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
        docs = self.vectorstore.similarity_search(query, k=k)
        return "\n".join([d.page_content for d in docs])

class SimilarQueriesRAG:
    def __init__(self, persist_directory: str = os.path.join(RAG_DIR, "query_cache_db")):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectorstore = None
        self.persist_directory = persist_directory

    def add_successful_query(self, query: str, sql: str):
        if not self.vectorstore:
            self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
        self.vectorstore.add_documents([Document(page_content=query, metadata={"sql": sql})])

    def retrieve_similar_queries(self, query: str, k: int = 3) -> str:
        if not self.vectorstore:
            try:
                self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
            except:
                return "No past examples available."
        docs = self.vectorstore.similarity_search(query, k=k)
        examples = ""
        for d in docs:
            examples += f"Question: {d.page_content}\nSQL: {d.metadata['sql']}\n\n"
        return examples

if __name__ == "__main__":
    # Initialization script
    s_rag = SchemaRAG()
    s_rag.initialize_from_metadata(os.path.join(DATA_DIR, "db_metadata.json"))
    
    g_rag = BusinessGlossaryRAG()
    g_rag.initialize_glossary()
    
    # Example table selection test
    selector = TableSelector(s_rag)
    # This requires ANTHROPIC_API_KEY to be set
    # results = selector.select_relevant_tables("Who are our top 10 customers by LTV?")
    # print(results)
