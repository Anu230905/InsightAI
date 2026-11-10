

import pandas as pd


class DataCleaningLab:

    def clean(
        self,
        df,
        missing_strategy="mean",
        remove_duplicates=True,
        trim_text=True,
        text_case="Keep original",
        fix_invalid=True
    ):

        # Always work on a separate copy
        cleaned_df = df.copy(deep=True)

        report = {
            "original_rows": len(df),
            "original_columns": len(df.columns),
            "duplicates_removed": 0,
            "missing_values_filled": 0,
            "rows_dropped": 0,
            "text_values_standardized": 0,
            "invalid_values_fixed": 0
        }

        # 1. Remove duplicate rows
        if remove_duplicates:
            before = len(cleaned_df)

            cleaned_df = cleaned_df.drop_duplicates()

            report["duplicates_removed"] = before - len(cleaned_df)

        # 2. Handle missing values
        if missing_strategy == "drop_rows":
            before = len(cleaned_df)

            cleaned_df = cleaned_df.dropna()

            report["rows_dropped"] = before - len(cleaned_df)

        elif missing_strategy != "leave":

            for column in cleaned_df.columns:

                missing_count = cleaned_df[column].isna().sum()

                if missing_count == 0:
                    continue

                if pd.api.types.is_numeric_dtype(cleaned_df[column]):

                    if missing_strategy == "mean":
                        fill_value = cleaned_df[column].mean()

                    elif missing_strategy == "median":
                        fill_value = cleaned_df[column].median()

                    elif missing_strategy == "mode":
                        modes = cleaned_df[column].mode()
                        fill_value = modes.iloc[0] if not modes.empty else None

                    else:
                        continue

                else:
                    modes = cleaned_df[column].mode()
                    fill_value = modes.iloc[0] if not modes.empty else None

                if fill_value is not None and pd.notna(fill_value):
                    cleaned_df[column] = cleaned_df[column].fillna(fill_value)
                    report["missing_values_filled"] += missing_count

        # 3. Standardize text formatting
        if trim_text:

            for column in cleaned_df.select_dtypes(
                include=["object", "string"]
            ).columns:

                original = cleaned_df[column].copy()

                cleaned_df[column] = cleaned_df[column].apply(
                    lambda value: value.strip()
                    if isinstance(value, str)
                    else value
                )

                if text_case == "Lowercase":
                    cleaned_df[column] = cleaned_df[column].apply(
                        lambda value: value.lower()
                        if isinstance(value, str)
                        else value
                    )

                elif text_case == "Uppercase":
                    cleaned_df[column] = cleaned_df[column].apply(
                        lambda value: value.upper()
                        if isinstance(value, str)
                        else value
                    )

                elif text_case == "Title Case":
                    cleaned_df[column] = cleaned_df[column].apply(
                        lambda value: value.title()
                        if isinstance(value, str)
                        else value
                    )

                report["text_values_standardized"] += int(
                    (original != cleaned_df[column]).sum()
                )

        # 4. Fix known invalid business values
        if fix_invalid:

            invalid_rules = {
                "Unit_Price": lambda s: s < 0,
                "Discount_Percent": lambda s: (s < 0) | (s > 100),
                "Quantity": lambda s: s <= 0
            }

            for column, rule in invalid_rules.items():

                if column in cleaned_df.columns:
                    numeric_values = pd.to_numeric(
                        cleaned_df[column], errors="coerce"
                    )

                    invalid_mask = rule(numeric_values)

                    report["invalid_values_fixed"] += int(
                        invalid_mask.sum()
                    )

                    cleaned_df.loc[invalid_mask, column] = pd.NA

        report["cleaned_rows"] = len(cleaned_df)
        report["cleaned_columns"] = len(cleaned_df.columns)
        report["remaining_missing_values"] = int(
            cleaned_df.isna().sum().sum()
        )

        return cleaned_df, report
