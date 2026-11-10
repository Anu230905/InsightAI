

import pandas as pd


class DataQualityDoctor:

    def analyze(self, df):

        report = {}

        # 1. Missing values
        missing = df.isnull().sum()
        missing = missing[missing > 0]
        report["missing_values"] = missing.to_dict()

        # 2. Duplicate rows
        duplicate_count = int(df.duplicated().sum())
        report["duplicates"] = duplicate_count

        # 3. Inconsistent text formatting
        formatting_issues = {}

        for col in df.select_dtypes(include=["object", "string"]).columns:

            values = df[col].dropna()

            inconsistent = values[
                values.astype(str).str.strip()
                != values.astype(str)
            ]

            if not inconsistent.empty:
                formatting_issues[col] = (
                    inconsistent.astype(str).unique().tolist()
                )

            # Check capitalization differences
            normalized = values.astype(str).str.strip().str.lower()

            if normalized.nunique() < values.nunique():
                formatting_issues[col] = (
                    formatting_issues.get(col, [])
                    + ["Possible capitalization inconsistency"]
                )

        report["formatting_issues"] = formatting_issues

        # 4. Numeric outlier detection using IQR
        outliers = {}

        numeric_columns = df.select_dtypes(
            include=["number"]
        ).columns

        for col in numeric_columns:

            values = df[col].dropna()

            if len(values) < 4:
                continue

            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1

            lower_limit = q1 - 1.5 * iqr
            upper_limit = q3 + 1.5 * iqr

            unusual = values[
                (values < lower_limit) |
                (values > upper_limit)
            ]

            if not unusual.empty:
                outliers[col] = {
                    "count": int(len(unusual)),
                    "values": unusual.head(10).tolist()
                }

        report["outliers"] = outliers

        # 5. Business rule validation
        invalid_values = {}

        if "Unit_Price" in df.columns:
            count = int((df["Unit_Price"] < 0).sum())
            if count:
                invalid_values["Unit_Price"] = (
                    f"{count} negative price value(s)"
                )

        if "Discount_Percent" in df.columns:
            count = int(
                (
                    (df["Discount_Percent"] < 0) |
                    (df["Discount_Percent"] > 100)
                ).sum()
            )
            if count:
                invalid_values["Discount_Percent"] = (
                    f"{count} invalid discount value(s)"
                )

        if "Quantity" in df.columns:
            count = int((df["Quantity"] <= 0).sum())
            if count:
                invalid_values["Quantity"] = (
                    f"{count} zero or negative quantity value(s)"
                )

        report["invalid_values"] = invalid_values

        return report
