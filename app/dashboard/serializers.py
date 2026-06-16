def build_plotly_series(rows: list[dict]) -> list[dict]:
    grouped = {}
    for row in rows:
        key = row["standard_line_item"]
        grouped.setdefault(key, {"name": key, "x": [], "y": []})
        grouped[key]["x"].append(row["year_label"])
        grouped[key]["y"].append(float(row["value"]))
    return list(grouped.values())
