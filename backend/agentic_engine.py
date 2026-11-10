


import json
import re
import urllib.request
import urllib.error

import pandas as pd

from backend.quality import DataQualityDoctor
from backend.sql_analytics import SQLAnalytics


class AgenticDataAnalyst:

    def __init__(
        self,
        db_engine,
        model="qwen2.5:1.5b",
        host="http://localhost:11434",
        max_steps=4
    ):
        self.db_engine = db_engine
        self.model = model
        self.host = host.rstrip("/")
        self.max_steps = max_steps

        self.analytics = SQLAnalytics(db_engine)

        self.tools = {
            "dataset_overview": self.dataset_overview,
            "column_statistics": self.column_statistics,
            "data_quality": self.data_quality,
            "run_sql": self.run_sql
        }

    # ==================================================
    # 1. GET DATASET
    # ==================================================

    def get_dataframe(self):

        df = self.db_engine.get_data()

        if df is None or df.empty:
            raise ValueError("The uploaded dataset is empty.")

        return df

    # ==================================================
    # 2. OLLAMA CONNECTION
    # ==================================================

    def ask_model(self, messages):

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
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
                timeout=240
            ) as response:

                result = json.loads(
                    response.read().decode("utf-8")
                )

        except urllib.error.URLError as error:

            raise ConnectionError(
                "Cannot connect to Ollama. "
                "Please make sure Ollama is running."
            ) from error

        except Exception as error:

            raise RuntimeError(
                f"Ollama request failed: {error}"
            ) from error

        content = (
            result.get("message", {})
            .get("content", "")
            .strip()
        )

        if not content:
            raise ValueError(
                "The AI returned an empty response."
            )

        return content

    # ==================================================
    # 3. JSON PARSER
    # ==================================================

    @staticmethod
    def parse_json(content):

        content = content.strip()

        content = re.sub(
            r"^```(?:json)?\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"\s*```$",
            "",
            content
        )

        try:
            return json.loads(content)

        except json.JSONDecodeError:

            match = re.search(
                r"\{.*\}",
                content,
                flags=re.DOTALL
            )

            if match:
                return json.loads(match.group(0))

            raise ValueError(
                "The AI did not return valid JSON."
            )

    # ==================================================
    # 4. DATASET OVERVIEW TOOL
    # ==================================================

    def dataset_overview(self, arguments=None):

        df = self.get_dataframe()

        return {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "columns": [
                {
                    "name": str(column),
                    "data_type": str(df[column].dtype)
                }
                for column in df.columns
            ],
            "missing_values": {
                str(column): int(count)
                for column, count in df.isnull().sum().items()
                if count > 0
            },
            "duplicate_rows": int(df.duplicated().sum())
        }

    # ==================================================
    # 5. COLUMN STATISTICS TOOL
    # ==================================================

    def column_statistics(self, arguments):

        df = self.get_dataframe()

        column = arguments.get("column")

        if not column or column not in df.columns:
            return {
                "error": "Invalid column name."
            }

        if not pd.api.types.is_numeric_dtype(df[column]):
            return {
                "error": "Selected column is not numerical."
            }

        series = df[column]

        return {
            "column": column,
            "count": int(series.count()),
            "mean": self.safe_number(series.mean()),
            "median": self.safe_number(series.median()),
            "minimum": self.safe_number(series.min()),
            "maximum": self.safe_number(series.max()),
            "standard_deviation": self.safe_number(series.std()),
            "total": self.safe_number(series.sum())
        }

    @staticmethod
    def safe_number(value):

        if pd.isna(value):
            return None

        return round(float(value), 2)

    # ==================================================
    # 6. DATA QUALITY TOOL
    # ==================================================

    def data_quality(self, arguments=None):

        df = self.get_dataframe()

        doctor = DataQualityDoctor()

        report = doctor.analyze(df)

        return report

    # ==================================================
    # 7. SQL EXECUTION TOOL
    # ==================================================

    def run_sql(self, arguments):

        query = arguments.get("query", "")

        if not query:
            return {
                "error": "No SQL query was generated."
            }

        result = self.analytics.execute_query(query)

        preview = result.head(30)

        return {
            "columns": preview.columns.tolist(),
            "rows": preview.to_dict(orient="records"),
            "total_result_rows": int(len(result)),
            "truncated": len(result) > 30
        }

    # ==================================================
    # 8. AVAILABLE TOOLS
    # ==================================================

    def get_tool_descriptions(self):

        return [
            {
                "name": "dataset_overview",
                "description": (
                    "Inspect the dataset structure, "
                    "columns, missing values and duplicates."
                ),
                "arguments": {}
            },
            {
                "name": "column_statistics",
                "description": (
                    "Calculate mean, median, minimum, "
                    "maximum, total and standard deviation "
                    "for a numerical column."
                ),
                "arguments": {
                    "column": "Exact numerical column name"
                }
            },
            {
                "name": "data_quality",
                "description": (
                    "Detect missing values, duplicates, "
                    "outliers, formatting issues and invalid values."
                ),
                "arguments": {}
            },
            {
                "name": "run_sql",
                "description": (
                    "Execute a DuckDB SELECT query on uploaded_data. "
                    "Use this for revenue, sales, rankings, "
                    "group comparisons and aggregations."
                ),
                "arguments": {
                    "query": "A valid SELECT SQL query"
                }
            }
        ]

    # ==================================================
    # 9. SQL IDENTIFIER HELPER
    # ==================================================

    @staticmethod
    def quote_identifier(name):

        return '"' + str(name).replace('"', '""') + '"'

    # ==================================================
    # 10. AUTOMATIC COLUMN DETECTION
    # ==================================================

    def find_column(self, keywords, columns):

        for column in columns:

            normalized = re.sub(
                r"[^a-z0-9]",
                "",
                str(column).lower()
            )

            for keyword in keywords:

                if keyword in normalized:
                    return column

        return None

    # ==================================================
    # 11. AUTOMATIC SQL FALLBACK
    # ==================================================

    def fallback_sql(self, question):

        df = self.get_dataframe()

        columns = list(df.columns)

        numeric_columns = df.select_dtypes(
            include="number"
        ).columns.tolist()

        categorical_columns = [
            column
            for column in df.columns
            if (
                df[column].dtype == "object"
                or isinstance(
                    df[column].dtype,
                    pd.CategoricalDtype
                )
            )
            and df[column].nunique() <= 100
        ]

        q = question.lower()

        revenue_column = self.find_column(
            ["revenue", "salesamount", "totalamount", "sellingprice"],
            numeric_columns
        )

        quantity_column = self.find_column(
            ["quantity", "unitsold", "unitssold", "sold"],
            numeric_columns
        )

        cost_column = self.find_column(
            ["purchasecost", "unitcost", "costprice", "cost"],
            numeric_columns
        )

        product_column = self.find_column(
            ["phonemodel", "productname", "product", "model", "item"],
            columns
        )

        region_column = self.find_column(
            ["region", "location", "city", "state", "area"],
            columns
        )

        date_column = self.find_column(
            ["date", "salesdate", "orderdate", "transactiondate"],
            columns
        )

        # Revenue or sales by product
        if any(word in q for word in [
            "revenue", "sales", "top", "highest", "best selling"
        ]):

            if revenue_column and product_column:

                revenue = self.quote_identifier(revenue_column)
                product = self.quote_identifier(product_column)

                return {
                    "tool": "run_sql",
                    "arguments": {
                        "query": (
                            f"SELECT {product}, "
                            f"SUM({revenue}) AS total_revenue "
                            f"FROM uploaded_data "
                            f"GROUP BY {product} "
                            f"ORDER BY total_revenue DESC "
                            f"LIMIT 5"
                        )
                    },
                    "reason": "Rank products by total revenue."
                }

            if quantity_column and product_column:

                quantity = self.quote_identifier(quantity_column)
                product = self.quote_identifier(product_column)

                return {
                    "tool": "run_sql",
                    "arguments": {
                        "query": (
                            f"SELECT {product}, "
                            f"SUM({quantity}) AS total_units_sold "
                            f"FROM uploaded_data "
                            f"GROUP BY {product} "
                            f"ORDER BY total_units_sold DESC "
                            f"LIMIT 5"
                        )
                    },
                    "reason": "Rank products by units sold."
                }

        # Regional comparison
        if any(word in q for word in [
            "region", "location", "city", "state"
        ]):

            if region_column and revenue_column:

                region = self.quote_identifier(region_column)
                revenue = self.quote_identifier(revenue_column)

                return {
                    "tool": "run_sql",
                    "arguments": {
                        "query": (
                            f"SELECT {region}, "
                            f"SUM({revenue}) AS total_revenue "
                            f"FROM uploaded_data "
                            f"GROUP BY {region} "
                            f"ORDER BY total_revenue DESC"
                        )
                    },
                    "reason": "Compare revenue across regions."
                }

        # Profit calculation
        if "profit" in q:

            if cost_column and revenue_column:

                cost = self.quote_identifier(cost_column)
                revenue = self.quote_identifier(revenue_column)

                if quantity_column:

                    quantity = self.quote_identifier(quantity_column)

                    profit_expression = (
                        f"SUM(({revenue} - {cost}) * {quantity})"
                    )

                else:

                    profit_expression = (
                        f"SUM({revenue} - {cost})"
                    )

                return {
                    "tool": "run_sql",
                    "arguments": {
                        "query": (
                            f"SELECT {profit_expression} AS total_profit "
                            f"FROM uploaded_data"
                        )
                    },
                    "reason": "Calculate profit from available sales and cost columns."
                }

        # Monthly sales trend
        if any(word in q for word in [
            "monthly", "month", "trend", "over time"
        ]):

            if date_column and revenue_column:

                date = self.quote_identifier(date_column)
                revenue = self.quote_identifier(revenue_column)

                return {
                    "tool": "run_sql",
                    "arguments": {
                        "query": (
                            f"SELECT DATE_TRUNC('month', "
                            f"TRY_CAST({date} AS DATE)) AS sales_month, "
                            f"SUM({revenue}) AS total_revenue "
                            f"FROM uploaded_data "
                            f"GROUP BY sales_month "
                            f"ORDER BY sales_month"
                        )
                    },
                    "reason": "Analyse monthly revenue trends."
                }

        # General numerical statistics
        if numeric_columns:

            target = self.find_column(
                ["revenue", "sales", "price", "quantity", "amount"],
                numeric_columns
            )

            if target is None:
                target = numeric_columns[0]

            return {
                "tool": "column_statistics",
                "arguments": {
                    "column": target
                },
                "reason": "Calculate numerical statistics."
            }

        return {
            "tool": "dataset_overview",
            "arguments": {},
            "reason": "Inspect the uploaded dataset."
        }

    # ==================================================
    # 12. FINAL ANSWER GENERATION
    # ==================================================

    def generate_final_answer(self, question, history):

        messages = [
            {
                "role": "system",
                "content": (
                    "You are InsightAI, a business data analyst. "
                    "Answer using only the supplied tool results. "
                    "Do not invent values. Explain findings clearly. "
                    "Give practical recommendations when supported. "
                    "Mention when a metric could not be calculated. "
                    "Return a JSON object with an answer field."
                )
            },
            {
                "role": "user",
                "content": (
                    "User question:\n"
                    + question
                    + "\n\nTool execution results:\n"
                    + json.dumps(history, default=str)
                    + "\n\nWrite a clear final answer based on these results."
                )
            }
        ]

        try:

            response = self.ask_model(messages)

            parsed = self.parse_json(response)

            answer = parsed.get("answer")

            if answer and not re.search(
                r"provide (the )?(sql|query)|give me the sql",
                answer,
                flags=re.IGNORECASE
            ):
                return answer

        except Exception:
            pass

        # Reliable fallback if the model cannot summarise.
        lines = [
            "Analysis completed using the available dataset tools.",
            ""
        ]

        for item in history:

            lines.append(
                f"Step {item['step']}: {item['tool']}"
            )

            lines.append(
                json.dumps(item["result"], indent=2, default=str)
            )

            lines.append("")

        lines.append(
            "Review the execution results above. "
            "Recommendations are limited to the available data."
        )

        return "\n".join(lines)

    # ==================================================
    # 13. MAIN AGENT LOOP
    # ==================================================

    def analyse(self, question):

        if not question or not question.strip():

            raise ValueError(
                "Please enter a question."
            )

        df = self.get_dataframe()

        schema = "\n".join(
            f"- {column}: {df[column].dtype}"
            for column in df.columns
        )

        tool_descriptions = self.get_tool_descriptions()

        system_prompt = f"""
You are InsightAI, an agentic data analyst.

You must analyse the user's uploaded dataset.

DATASET SCHEMA:
{schema}

AVAILABLE TOOLS:
{json.dumps(tool_descriptions, indent=2)}

STRICT RULES:

1. Never ask the user to provide SQL.
2. You must generate SQL yourself when required.
3. Use exact column names from the schema.
4. SQL must be SELECT or WITH only.
5. The table name is uploaded_data.
6. Use the available tools to obtain real results.
7. Never invent numerical results.
8. You can call one tool at a time.
9. Review the result before choosing the next tool.
10. Stop when enough information is available.

To use a tool, return:

{{
  "action": "tool",
  "tool": "run_sql",
  "arguments": {{
    "query": "SELECT ... FROM uploaded_data"
  }},
  "reason": "Reason for this query"
}}

To finish, return:

{{
  "action": "final",
  "answer": "Your findings and recommendations"
}}

IMPORTANT:
Do not tell the user to write SQL.
You are responsible for selecting and executing the tools.

Return only valid JSON.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ]

        history = []
        used_tools = set()

        for step in range(self.max_steps):

            decision = None

            try:

                raw_response = self.ask_model(messages)

                decision = self.parse_json(raw_response)

            except Exception:
                decision = None

            # ------------------------------------------
            # MODEL FAILED OR ASKED USER FOR SQL
            # ------------------------------------------

            if (
                not isinstance(decision, dict)
                or decision.get("action") != "tool"
                or decision.get("tool") not in self.tools
            ):

                fallback = self.fallback_sql(question)

                tool_name = fallback["tool"]
                arguments = fallback["arguments"]
                reason = fallback["reason"]

            else:

                tool_name = decision.get("tool")
                arguments = decision.get("arguments", {})
                reason = decision.get("reason", "")

                if not isinstance(arguments, dict):
                    arguments = {}

                # Avoid repeating the exact same tool call.
                signature = (
                    tool_name,
                    json.dumps(arguments, sort_keys=True)
                )

                if signature in used_tools:

                    fallback = self.fallback_sql(question)

                    tool_name = fallback["tool"]
                    arguments = fallback["arguments"]
                    reason = fallback["reason"]

                else:

                    used_tools.add(signature)

            # ------------------------------------------
            # EXECUTE SELECTED TOOL
            # ------------------------------------------

            try:

                tool_result = self.tools[tool_name](
                    arguments
                )

            except Exception as error:

                tool_result = {
                    "error": str(error)
                }

            history.append({
                "step": step + 1,
                "tool": tool_name,
                "reason": reason,
                "arguments": arguments,
                "result": tool_result
            })

            # ------------------------------------------
            # PROVIDE RESULT TO LOCAL MODEL
            # ------------------------------------------

            messages.append({
                "role": "assistant",
                "content": json.dumps({
                    "action": "tool",
                    "tool": tool_name,
                    "arguments": arguments,
                    "reason": reason
                })
            })

            messages.append({
                "role": "user",
                "content": (
                    "Tool execution result:\n"
                    + json.dumps(
                        tool_result,
                        default=str
                    )
                    + "\nReview the result. "
                    "Choose another useful tool if necessary. "
                    "Otherwise return your final answer as JSON. "
                    "Never ask the user to provide SQL."
                )
            })

            # Stop if a tool returns an error.
            if isinstance(tool_result, dict) and "error" in tool_result:
                break

        # ----------------------------------------------
        # GENERATE FINAL ANSWER
        # ----------------------------------------------

        final_answer = self.generate_final_answer(
            question,
            history
        )

        return {
            "answer": final_answer,
            "steps": history,
            "completed": len(history) > 0
        }
