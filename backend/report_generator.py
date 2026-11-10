

import json
import urllib.request
import urllib.error
import pandas as pd


class AIReportGenerator:

    def __init__(
        self,
        model="qwen2.5:1.5b",
        host="http://localhost:11434"
    ):
        self.model = model
        self.host = host.rstrip("/")

    def create_dataset_summary(self, df):

        if df is None or df.empty:
            raise ValueError("The dataset is empty.")

        summary = {
            "total_rows": int(df.shape[0]),
            "total_columns": int(df.shape[1]),
            "column_names": df.columns.tolist(),
            "data_types": {
                str(column): str(dtype)
                for column, dtype in df.dtypes.items()
            },
            "missing_values": {
                str(column): int(count)
                for column, count in df.isnull().sum().items()
                if count > 0
            },
            "duplicate_rows": int(df.duplicated().sum()),
            "numerical_summary": {}
        }

        numeric_df = df.select_dtypes(include="number")

        for column in numeric_df.columns:

            series = numeric_df[column]

            summary["numerical_summary"][str(column)] = {
                "mean": self._safe_number(series.mean()),
                "median": self._safe_number(series.median()),
                "minimum": self._safe_number(series.min()),
                "maximum": self._safe_number(series.max()),
                "standard_deviation": self._safe_number(series.std())
            }

        return summary

    @staticmethod
    def _safe_number(value):

        if pd.isna(value):
            return None

        return round(float(value), 3)

    def generate_report(self, df):

        summary = self.create_dataset_summary(df)

        prompt = f"""
You are a professional data analyst.

Create a clear and structured analytical report
using ONLY the dataset information provided below.

DATASET INFORMATION:
{json.dumps(summary, indent=2, default=str)}

Write the report using these sections:

1. Executive Summary
2. Dataset Overview
3. Data Quality Assessment
4. Numerical Analysis
5. Key Observations
6. Recommendations
7. Conclusion

Instructions:
- Use simple professional language.
- Explain important numerical statistics.
- Mention missing values and duplicate records.
- Do not invent patterns or relationships.
- Do not claim correlation or causation unless supported.
- If information is insufficient, clearly mention it.
- Recommendations must be based on the available summary.
- Return the report as readable plain text.
"""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a careful data analyst. "
                        "Use only the supplied dataset summary. "
                        "Never invent data or findings."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.2
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
                "The AI model took too long to generate the report. "
                "Try again."
            ) from error

        except Exception as error:

            raise RuntimeError(
                f"Report generation failed: {error}"
            ) from error

        report = (
            response_data
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not report:
            raise ValueError(
                "The AI model returned an empty report."
            )

        return report
