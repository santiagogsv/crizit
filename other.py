import pandas as pd
import numpy as np


def check_lines(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    group_col: str,
    df1_label: str,
    df2_label: str,
    suffixes: tuple = ("_1", "_2"),
) -> pd.DataFrame:
    count1 = df1.groupby(group_col).size().reset_index(name=f"count{suffixes[0]}")
    count2 = df2.groupby(group_col).size().reset_index(name=f"count{suffixes[1]}")
    merged = pd.merge(count1, count2, on=group_col, how="outer").fillna(0)
    merged["error"] = np.where(
        merged[f"count{suffixes[0]}"] != merged[f"count{suffixes[1]}"],
        "Count differs",
        "Match",
    )
    discrepancies = merged[merged["error"] != "Match"].copy()
    if not discrepancies.empty:
        print(
            f"Comparing {df1_label} and {df2_label}:\n{discrepancies.to_string(index=False)}"
        )
    return discrepancies
