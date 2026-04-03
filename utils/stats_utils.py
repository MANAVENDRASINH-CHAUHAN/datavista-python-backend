from __future__ import annotations

import pandas as pd


def build_basic_stats(dataframe: pd.DataFrame) -> dict:
    missing_values = []
    for column in dataframe.columns:
        missing_values.append(
            {
                "column": column,
                "missingCount": int(dataframe[column].isna().sum()),
            }
        )

    numeric_df = dataframe.select_dtypes(include="number")
    numeric_summary = {}
    for column in numeric_df.columns:
        series = numeric_df[column].dropna()
        if series.empty:
            numeric_summary[column] = {
                "count": 0,
                "mean": 0,
                "min": 0,
                "max": 0,
                "sum": 0,
            }
            continue

        numeric_summary[column] = {
            "count": int(series.count()),
            "mean": round(float(series.mean()), 4),
            "min": round(float(series.min()), 4),
            "max": round(float(series.max()), 4),
            "sum": round(float(series.sum()), 4),
        }

    column_types = [{"column": column, "type": str(dataframe[column].dtype)} for column in dataframe.columns]

    return {
        "rowCount": int(len(dataframe)),
        "columnCount": int(len(dataframe.columns)),
        "missingValues": missing_values,
        "duplicateRows": int(dataframe.duplicated().sum()),
        "numericSummary": numeric_summary,
        "columnTypes": column_types,
        "numericColumns": list(numeric_df.columns),
    }


def build_chart_data(dataframe: pd.DataFrame, x_axis: str = "", y_axis: str = "") -> dict:
    if dataframe.empty or dataframe.shape[1] == 0:
        return {"xAxis": x_axis, "yAxis": y_axis, "barLineData": [], "pieData": []}

    columns = list(dataframe.columns)
    numeric_columns = list(dataframe.select_dtypes(include="number").columns)

    if not x_axis or x_axis not in columns:
        x_axis = columns[0]

    if not y_axis or y_axis not in numeric_columns:
        y_axis = numeric_columns[0] if numeric_columns else ""

    if y_axis:
        grouped = (
            dataframe[[x_axis, y_axis]]
            .dropna(subset=[x_axis])
            .groupby(x_axis, dropna=False)[y_axis]
            .mean()
            .reset_index()
            .head(8)
        )

        bar_line_data = [
            {"label": str(row[x_axis]), "value": round(float(row[y_axis]), 4)}
            for _, row in grouped.iterrows()
        ]
    else:
        counts = dataframe[x_axis].fillna("Missing").astype(str).value_counts().head(8)
        bar_line_data = [{"label": str(index), "value": int(value)} for index, value in counts.items()]

    pie_data = [{"name": item["label"], "value": item["value"]} for item in bar_line_data]

    return {
        "xAxis": x_axis,
        "yAxis": y_axis,
        "barLineData": bar_line_data,
        "pieData": pie_data,
    }
