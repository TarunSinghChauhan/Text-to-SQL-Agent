# Senior Data Scientist Interview Preparation

## 1. How does schema-aware RAG improve Text-to-SQL accuracy over zero-shot prompting?
Schema-aware RAG solves the **Context Window Overflow** and **Hallucination** problems. In zero-shot prompting, you must either include the entire schema (which fails as table counts grow) or risk the LLM guessing column names. RAG retrieves only the tables relevant to the specific user intent. By including **sample values** and **business descriptions** in the vector index, the LLM gains "domain intuition"—understanding that a column like `plan_tier` contains ['Free', 'Pro']—which prevents syntactically correct but logically incorrect queries.

## 2. How does the self-correction loop work and what is the retry limit?
The loop uses a **Validation-Execution-Feedback** cycle. First, we parse the SQL with `sqlglot` to catch syntax errors without hitting the DB. If it fails, or if the DB returns an error, we feed the **Error Message + Failed SQL** back to the LLM. I've implemented a limit of **3 retries**. Beyond 3 attempts, the marginal gain in success rate drops significantly, and we risk "failing loudly"—it's better to explain the failure to the user than to produce increasingly complex, incorrect SQL.

## 3. Execution Accuracy vs. Exact Match Accuracy?
**Exact Match (EM)** measures if the generated SQL is string-identical to the "gold" query. This is often too rigid because there are many ways to write a correct SQL (e.g., different join orders, CTEs vs. subqueries). **Execution Accuracy (EX)** measures if the result set matches the gold standard. EX is much more meaningful in a business context because it validates the logic, though it requires a live database to test.

## 4. How do you handle ambiguous queries?
Our `classify_query_intent` tool identifies "ambiguous" queries. Instead of guessing, the agent is designed to return a clarification request to the user. For example, if a user asks "Compare Sales," we ask if they mean by region, by month, or by product category. This mimics the behavior of a senior data scientist who clarifies requirements before building a dashboard.

## 5. What are Cartesian Products and how does your tool detect them?
A Cartesian Product (Cross Join) occurs when two tables are joined without a matching condition, resulting in every row of Table A being paired with every row of Table B (N x M). This can crash a warehouse. Our validation tool uses the `sqlglot` AST to traverse the join nodes; if a `JOIN` exists without a corresponding `ON` or `USING` clause, it flags the query as invalid before execution.

## 6. How would you support write operations (INSERT/UPDATE) safely?
Safety first:
1.  **RBAC**: Use a database user with read-only permissions for general users.
2.  **Audit Logging**: Every write operation must be logged with the user's ID and the LLM's reasoning.
3.  **Human-in-the-Loop**: The agent should never execute a write automatically. It generates the SQL, explains the impact (e.g., "This will update 500 rows"), and requires a manual "Approve" button click.

## 7. How does conversation memory work across turns?
We use a **Redis-backed state manager**. We preserve the list of "Selected Tables" from the previous turn to maintain context. If the user says "Filter this by UK," we don't re-run RAG; we reuse the existing schema context and previous SQL as a few-shot example for the next generation.

## 8. How would you replace Claude with a smaller model like CodeLlama?
To achieve Claude-level performance with a 7B or 13B model:
1.  **Fine-tuning**: Use QLoRA on the Spider and BIRD datasets.
2.  **Prompt Engineering**: Shift from Chain-of-Thought (which smaller models struggle with) to more rigid, template-based few-shot examples.
3.  **Distillation**: Use Claude to generate "Rationales" for 5,000 queries and train the smaller model to mimic that reasoning.

## 9. Handling a database with 500 tables?
This is where our **Multi-Stage Retrieval** excels.
- **Stage 1 (Vector Search)**: Narrow 500 tables down to top 20 based on semantic similarity.
- **Stage 2 (LLM Pruning)**: Feed the 20 table names/descriptions to a fast model (Gemini Flash or GPT-4o-mini) to pick the final 3-5 tables.
- **Stage 3 (Full Context)**: Only then do we inject the full column-level metadata for the final few tables into the prompt.

## 10. Prevention of Prompt Injection?
1.  **Read-Only User**: The most critical defense is the DB-level permission.
2.  **SQL Parsing**: Using `sqlglot` to verify that the query only contains `SELECT` statements.
3.  **System Prompt Hardening**: Instruct the LLM to ignore any instructions within the "User Question" that attempt to bypass system rules or reveal schema details not retrieved by RAG.
