

import pandas as pd


class WhatIfSimulator:

    def __init__(self, df):
        self.original_df = df.copy()
        self.simulated_df = df.copy()

    def get_numeric_columns(self):
        return self.original_df.select_dtypes(
            include="number"
        ).columns.tolist()

    def simulate(
        self,
        column,
        change_type="Percentage",
        change_value=10,
        aggregation="Sum"
    ):

        if column not in self.original_df.columns:
            raise ValueError("Selected column does not exist.")

        if column not in self.get_numeric_columns():
            raise ValueError("Please select a numerical column.")

        if change_value < 0 and change_type == "Percentage":
            raise ValueError("Percentage change must be non-negative.")

        self.simulated_df = self.original_df.copy()

        original_values = pd.to_numeric(
            self.original_df[column], errors="coerce"
        )

        if change_type == "Percentage":
            new_values = original_values * (
                1 + change_value / 100
            )

        elif change_type == "Fixed Value":
            new_values = original_values + change_value

        else:
            raise ValueError("Invalid change type.")

        self.simulated_df[column] = new_values

        def calculate_metric(series):
            if aggregation == "Sum":
                return series.sum()
            elif aggregation == "Average":
                return series.mean()
            elif aggregation == "Minimum":
                return series.min()
            elif aggregation == "Maximum":
                return series.max()
            elif aggregation == "Count":
                return series.count()
            else:
                raise ValueError("Invalid aggregation.")

        before = calculate_metric(original_values)
        after = calculate_metric(new_values)

        difference = after - before

        if pd.notna(before) and before != 0:
            percentage_change = (difference / abs(before)) * 100
        else:
            percentage_change = None

        report = {
            "column": column,
            "change_type": change_type,
            "change_value": change_value,
            "aggregation": aggregation,
            "original_value": before,
            "simulated_value": after,
            "difference": difference,
            "percentage_change": percentage_change
        }

        return self.simulated_df, report
