

import duckdb
import pandas as pd
from io import BytesIO

class DataEngine:

    def __init__(self):
        self.conn = duckdb.connect(database=":memory:")
        self.table_name = "uploaded_data"

    def load_file(self, file_buffer, filename):

        extension = filename.lower().split(".")[-1]

        # Convert uploaded bytes into a file-like object
        file_object = BytesIO(file_buffer)

        if extension == "csv":
            df = pd.read_csv(file_object)

        elif extension in ["xls", "xlsx"]:
            df = pd.read_excel(file_object)

        else:
            raise ValueError("Unsupported file format.")

        if df.empty:
            raise ValueError("The uploaded file contains no data.")

        self.conn.register("temp_df", df)

        self.conn.execute(
            f"CREATE OR REPLACE TABLE {self.table_name} AS SELECT * FROM temp_df"
        )

        self.conn.unregister("temp_df")

        return df

    def get_summary_stats(self):

        columns_df = self.conn.execute(
            f"DESCRIBE {self.table_name}"
        ).fetchdf()

        row_count = self.conn.execute(
            f"SELECT COUNT(*) FROM {self.table_name}"
        ).fetchone()[0]

        missing_stats = {}

        for col in columns_df["column_name"]:

            safe_col = col.replace('"', '""')

            missing_count = self.conn.execute(
                f'SELECT COUNT(*) FROM {self.table_name} WHERE "{safe_col}" IS NULL'
            ).fetchone()[0]

            missing_stats[col] = missing_count

        return {
            "row_count": row_count,
            "columns": columns_df,
            "missing_values": missing_stats
        }

    def get_preview(self, limit=10):

        return self.conn.execute(
            f"SELECT * FROM {self.table_name} LIMIT {int(limit)}"
        ).fetchdf()

    def get_data(self):

        return self.conn.execute(
            f"SELECT * FROM {self.table_name}"
        ).fetchdf()

    def close(self):
        self.conn.close()
