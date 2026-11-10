

import pandas as pd
import numpy as np


class RootCauseAnalyzer:
    """
    Statistical root-cause exploration for a numerical business metric.

    The analyzer identifies:
    1. Numerical features associated with the target metric.
    2. Categorical groups whose average target value differs from
       the overall average.
    """

    def __init__(self, df):
        self.df = df.copy()

    def get_numeric_columns(self):
        return self.df.select_dtypes(include=np.number).columns.tolist()

    def get_categorical_columns(self):
        columns = self.df.select_dtypes(
            include=["object", "category", "bool"]
        ).columns.tolist()

        # Exclude columns with too many unique values.
        return [
            col for col in columns
            if 1 < self.df[col].nunique(dropna=True) <= 50
        ]

    def analyze(
        self,
        target_column,
        direction="Both",
        min_group_size=5
    ):
        if target_column not in self.df.columns:
            raise ValueError("The selected target column does not exist.")

        if target_column not in self.get_numeric_columns():
            raise ValueError(
                "Please select a numerical target column for this analysis."
            )

        data = self.df.copy()
        data[target_column] = pd.to_numeric(
            data[target_column], errors="coerce"
        )
        data = data.dropna(subset=[target_column])

        if data.empty:
            raise ValueError(
                "The target column does not contain usable numerical values."
            )

        overall_mean = float(data[target_column].mean())
        overall_median = float(data[target_column].median())
        overall_std = float(data[target_column].std())

        if not np.isfinite(overall_mean):
            raise ValueError("Unable to calculate the target average.")

        if overall_std == 0 or not np.isfinite(overall_std):
            overall_std = 0.0

        # -------------------------------------------------
        # 1. Numerical feature correlation analysis
        # -------------------------------------------------
        numeric_results = []

        numeric_columns = [
            col for col in self.get_numeric_columns()
            if col != target_column
        ]

        for column in numeric_columns:
            pair = data[[column, target_column]].apply(
                pd.to_numeric, errors="coerce"
            ).dropna()

            if len(pair) < 3 or pair[column].nunique() < 2:
                continue

            correlation = pair[column].corr(pair[target_column])

            if pd.isna(correlation):
                continue

            numeric_results.append({
                "Feature": column,
                "Correlation": round(float(correlation), 4),
                "Relationship": (
                    "Positive" if correlation > 0
                    else "Negative" if correlation < 0
                    else "No linear relationship"
                ),
                "Rows Analyzed": len(pair)
            })

        numeric_df = pd.DataFrame(numeric_results)

        if not numeric_df.empty:
            numeric_df["Absolute Correlation"] = (
                numeric_df["Correlation"].abs()
            )
            numeric_df = numeric_df.sort_values(
                "Absolute Correlation", ascending=False
            ).reset_index(drop=True)

        # -------------------------------------------------
        # 2. Categorical group comparison
        # -------------------------------------------------
        categorical_results = []

        for column in self.get_categorical_columns():
            if column == target_column:
                continue

            grouped = (
                data.dropna(subset=[column])
                .groupby(column, observed=True)[target_column]
                .agg(["mean", "count"])
                .reset_index()
            )

            grouped = grouped[grouped["count"] >= min_group_size]

            for _, row in grouped.iterrows():
                group_mean = float(row["mean"])

                if overall_mean != 0:
                    deviation_percent = (
                        (group_mean - overall_mean)
                        / abs(overall_mean)
                    ) * 100
                else:
                    deviation_percent = np.nan

                difference = group_mean - overall_mean

                categorical_results.append({
                    "Feature": column,
                    "Group": str(row[column]),
                    "Group Average": round(group_mean, 3),
                    "Overall Average": round(overall_mean, 3),
                    "Difference": round(difference, 3),
                    "Deviation (%)": (
                        round(float(deviation_percent), 2)
                        if np.isfinite(deviation_percent)
                        else np.nan
                    ),
                    "Group Count": int(row["count"]),
                    "Direction": (
                        "Above average" if difference > 0
                        else "Below average" if difference < 0
                        else "Near average"
                    )
                })

        categorical_df = pd.DataFrame(categorical_results)

        if not categorical_df.empty:
            categorical_df["Absolute Deviation"] = (
                categorical_df["Difference"].abs()
            )

            if direction == "High":
                categorical_df = categorical_df[
                    categorical_df["Difference"] > 0
                ]
            elif direction == "Low":
                categorical_df = categorical_df[
                    categorical_df["Difference"] < 0
                ]

            categorical_df = categorical_df.sort_values(
                "Absolute Deviation", ascending=False
            ).reset_index(drop=True)

        # -------------------------------------------------
        # 3. Generate readable findings
        # -------------------------------------------------
        findings = []

        if not numeric_df.empty:
            top = numeric_df.iloc[0]

            findings.append(
                f"'{top['Feature']}' has the strongest numerical "
                f"correlation with '{target_column}' "
                f"(correlation: {top['Correlation']}). "
                "Correlation indicates association, not causation."
            )
        else:
            findings.append(
                "No suitable numerical feature correlations were found."
            )

        if not categorical_df.empty:
            top_group = categorical_df.iloc[0]

            findings.append(
                f"The group '{top_group['Group']}' in "
                f"'{top_group['Feature']}' has an average "
                f"'{target_column}' value of {top_group['Group Average']}, "
                f"compared with the overall average of "
                f"{top_group['Overall Average']}."
            )
        else:
            findings.append(
                "No categorical groups met the minimum group-size "
                "requirement for comparison."
            )

        return {
            "target_column": target_column,
            "row_count": len(data),
            "overall_mean": overall_mean,
            "overall_median": overall_median,
            "overall_std": overall_std,
            "numeric_analysis": numeric_df,
            "categorical_analysis": categorical_df,
            "findings": findings
        }
