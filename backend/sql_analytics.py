

import re


class SQLAnalytics:

    def __init__(self, db_engine):
        self.conn = db_engine.conn

    def validate_query(self, query):

        query = query.strip()

        if not query:
            return False, "Please enter a SQL query."

        # Allow only read-only queries
        if not re.match(r"^(SELECT|WITH)\b", query, re.IGNORECASE):
            return False, "Only SELECT and WITH queries are allowed."

        # Allow only one SQL statement
        if ";" in query.rstrip(";"):
            return False, "Multiple SQL statements are not allowed."

        # Block potentially destructive or administrative commands
        blocked_words = [
            "INSERT", "UPDATE", "DELETE", "DROP",
            "CREATE", "ALTER", "TRUNCATE", "COPY",
            "ATTACH", "DETACH", "INSTALL", "LOAD",
            "EXPORT", "IMPORT", "PRAGMA", "SET",
            "CALL", "EXECUTE", "EXEC"
        ]

        for word in blocked_words:
            pattern = rf"\b{word}\b"

            if re.search(pattern, query, re.IGNORECASE):
                return False, f"The SQL keyword '{word}' is not allowed."

        return True, "Query validated successfully."

    def execute_query(self, query):

        is_valid, message = self.validate_query(query)

        if not is_valid:
            raise ValueError(message)

        try:

            result = self.conn.execute(query).fetchdf()

            return result

        except Exception as error:

            raise RuntimeError(f"SQL execution failed: {error}")

    def get_columns(self):

        result = self.conn.execute(
            "DESCRIBE uploaded_data"
        ).fetchdf()

        return result

    def get_row_count(self):

        result = self.conn.execute(
            "SELECT COUNT(*) FROM uploaded_data"
        ).fetchone()

        return result[0]
