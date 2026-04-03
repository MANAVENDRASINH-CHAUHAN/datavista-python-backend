from __future__ import annotations

import pandas as pd


def detect_cleaning_issues(dataframe: pd.DataFrame) -> dict:
    missing_values = []
    for column in dataframe.columns:
        count = int(dataframe[column].isna().sum())
        if count > 0:
            missing_values.append({"column": column, "missingCount": count})

    duplicate_rows = int(dataframe.duplicated().sum())
    numeric_columns = list(dataframe.select_dtypes(include="number").columns)

    suggestions = []
    if duplicate_rows:
        suggestions.append(
            {
                "type": "dropDuplicates",
                "title": "Remove duplicate rows",
                "description": f"{duplicate_rows} duplicate rows were found and can be removed safely.",
            }
        )

    if missing_values:
        suggestions.append(
            {
                "type": "fillMissingValues",
                "title": "Fill missing values",
                "description": "Missing values were found. Numeric columns can use the mean and text columns can use a default label.",
            }
        )
        suggestions.append(
            {
                "type": "dropMissingValues",
                "title": "Drop rows with missing values",
                "description": "If incomplete rows are not useful, they can be removed.",
            }
        )

    if any(str(column).strip() != str(column) for column in dataframe.columns):
        suggestions.append(
            {
                "type": "trimColumnNames",
                "title": "Trim column names",
                "description": "Some column names have leading or trailing spaces.",
            }
        )

    suggestions.append(
        {
            "type": "cleanupDataTypes",
            "title": "Basic datatype cleanup",
            "description": "Try converting number-like text values into proper numeric columns.",
        }
    )

    return {
        "missingValues": missing_values,
        "duplicateRows": duplicate_rows,
        "numericColumns": numeric_columns,
        "suggestions": suggestions,
    }


def apply_cleaning_operations(dataframe: pd.DataFrame, operations: list) -> tuple[pd.DataFrame, list[str]]:
    cleaned_df = dataframe.copy()
    summaries: list[str] = []

    for operation in operations:
        if isinstance(operation, str):
            operation_type = operation
            operation_data = {}
        else:
            operation_type = operation.get("type", "")
            operation_data = operation

        if operation_type == "dropDuplicates":
            before = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates()
            removed = before - len(cleaned_df)
            summaries.append(f"Removed {removed} duplicate rows.")

        elif operation_type == "fillMissingValues":
            for column in cleaned_df.columns:
                if cleaned_df[column].isna().sum() == 0:
                    continue
                if pd.api.types.is_numeric_dtype(cleaned_df[column]):
                    cleaned_df[column] = cleaned_df[column].fillna(cleaned_df[column].mean())
                else:
                    cleaned_df[column] = cleaned_df[column].fillna("Unknown")
            summaries.append("Filled missing values using simple defaults.")

        elif operation_type == "dropMissingValues":
            before = len(cleaned_df)
            cleaned_df = cleaned_df.dropna()
            removed = before - len(cleaned_df)
            summaries.append(f"Dropped {removed} rows with missing values.")

        elif operation_type == "trimColumnNames":
            cleaned_df.columns = [str(column).strip() for column in cleaned_df.columns]
            summaries.append("Trimmed column names.")

        elif operation_type == "cleanupDataTypes":
            for column in cleaned_df.columns:
                if cleaned_df[column].dtype == object:
                    converted = pd.to_numeric(cleaned_df[column], errors="ignore")
                    cleaned_df[column] = converted
            summaries.append("Applied basic datatype cleanup.")

        elif operation_type == "renameColumn":
            source = operation_data.get("from", "").strip()
            target = operation_data.get("to", "").strip()
            if source and target and source in cleaned_df.columns:
                cleaned_df = cleaned_df.rename(columns={source: target})
                summaries.append(f"Renamed column {source} to {target}.")

        elif operation_type == "deleteColumn":
            column = operation_data.get("column", "").strip()
            if column and column in cleaned_df.columns:
                cleaned_df = cleaned_df.drop(columns=[column])
                summaries.append(f"Deleted column {column}.")

        elif operation_type == "fillMissingDefault":
            column = operation_data.get("column", "").strip()
            value = operation_data.get("value", "")
            if column and column in cleaned_df.columns:
                cleaned_df[column] = cleaned_df[column].fillna(value)
                summaries.append(f"Filled missing values in {column} with a default value.")

    if not summaries:
        summaries.append("No cleaning changes were applied.")

    return cleaned_df, summaries
