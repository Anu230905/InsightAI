


import json
import re
import urllib.request
import urllib.error


class NaturalLanguageSQL:
    """
    Converts natural-language questions into DuckDB SQL
    using a locally running Ollama model.
    """

    def __init__(
        self,
        db_engine,
        model="qwen2.5:1.5b",
        host="http://localhost:11434"
    ):
        self.db_engine = db_engine
        self.model = model
        self.host = host.rstrip("/")

    def get_schema(self):
        """Read the uploaded dataset's column names and data types."""

        columns = self.db_engine.conn.execute(
            "DESCRIBE uploaded_data"
        ).fetchall()

        schema = "\n".join(
            f"- {column[0]}: {column[1]}"
            for column in columns
        )

        return schema

    def generate_sql(self, question):
        """Ask Ollama to generate SQL for the user's question."""

        if not question or not question.strip():
            raise ValueError("Please enter a question.")

        schema = self.get_schema()

        prompt = f"""
You are a professional DuckDB SQL expert.

The user's uploaded dataset is stored in a DuckDB table
named uploaded_data.

DATASET SCHEMA:
{schema}

USER QUESTION:
{question}

INSTRUCTIONS:
1. Generate exactly one DuckDB SQL query.
2. Only generate SELECT or WITH queries.
3. Never generate INSERT, UPDATE, DELETE, DROP, CREATE,
   ALTER, TRUNCATE, COPY, ATTACH, DETACH or other
   data-modification or administrative statements.
4. Use only the columns listed in the dataset schema.
5. Use the exact column names, including spaces if present.
6. Use DuckDB-compatible SQL syntax.
7. Do not invent columns or tables.
8. Use meaningful aliases for calculated columns.
9. For requests asking for top or highest results,
   use ORDER BY and LIMIT.
10. For ordinary row-level results, use LIMIT 100.
11. Return only SQL, without Markdown or explanations.

SQL QUERY:
"""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You generate accurate, read-only "
                        "DuckDB SQL queries from natural-language "
                        "questions. Return only SQL."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0
            }
        }

        request = urllib.request.Request(
            url=f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=180
            ) as response:

                response_data = json.loads(
                    response.read().decode("utf-8")
                )

        except urllib.error.URLError as error:
            raise ConnectionError(
                "Could not connect to Ollama. "
                "Make sure Ollama is running."
            ) from error

        except TimeoutError as error:
            raise TimeoutError(
                "The local model took too long to respond. "
                "Try a shorter question."
            ) from error

        except Exception as error:
            raise RuntimeError(
                f"Ollama request failed: {error}"
            ) from error

        sql = (
            response_data.get("message", {})
            .get("content", "")
            .strip()
        )

        if not sql:
            raise ValueError(
                "The AI did not generate a SQL query."
            )

        # Remove Markdown code fences if returned.
        sql = re.sub(
            r"^```(?:sql)?\s*",
            "",
            sql,
            flags=re.IGNORECASE
        )

        sql = re.sub(r"\s*```$", "", sql).strip()

        # Remove a trailing semicolon only.
        sql = sql.rstrip(";").strip()

        return sql
