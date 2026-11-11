import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_DIR = BASE_DIR / "data" / "E-Commerce Sales Analytics.csv"

df = pd.read_csv(CSV_DIR)

VALUE_COLS = set(df.columns)
VALUE_AGG = {"sum", "mean", "count", "max", "min"}

# group_col: str  # 按哪列分组，比如 "product_category"
# value_col: str  # 对哪列计算，比如 "revenue"
# agg_func: str  # 聚合函数，"sum" / "mean" / "count" / "max" / "min"
# top_n: int = 5  # 返回前几行，默认5
def group_and_agg(group_col: str, value_col: str, agg_func: str, top_n: int = 5):
    if group_col not in VALUE_COLS:
        return {"error": f"{group_col}不是有效字段"}
    if value_col not in VALUE_COLS:
        return {"error": f"{value_col}不是有效字段"}
    if agg_func not in VALUE_AGG:
        return {"error": f"{agg_func}不是有效聚合函数"}

    result = df.groupby(group_col)[value_col].agg(agg_func).sort_values(ascending=False).head(top_n).reset_index().to_dict(orient="records")

    return {"result": result,
            "evidence": f"按{group_col}分组， 对{value_col}求{agg_func}，共{top_n}行"}

# filter_col: str       # 筛选哪列，比如 "region"
# filter_val: str       # 筛选值，比如 "East"
# value_col: str        # 对哪列统计，比如 "revenue"
# agg_func: str         # 聚合函数，同上
def filter_and_agg(filter_col: str, filter_val: str, value_col: str, agg_func: str) -> dict:
    if filter_col not in VALUE_COLS:
        return {"error": f"{filter_val}不是有效字段"}
    if value_col not in VALUE_COLS:
        return {"error": f"{value_col}不是有效字段"}
    if agg_func not in VALUE_AGG:
        return {"error": f"{agg_func}不是有效聚合函数"}

    filtered = df[df[filter_col] == filter_val]
    if len(filtered) == 0:
        return {"error": "没有找到匹配的数据"}

    result = filtered[value_col].agg(agg_func)
    return {"result": {value_col: round(float(result), 2)},
            "evidence": f"筛选{filter_col}={filter_val}，共{len(filtered)}行，求{agg_func}"}

def get_summary() -> dict:
    return {
        "result": {
            "总行数": len(df),
            "品类": df["product_category"].unique().tolist(),
            "地区": df["region"].unique().tolist(),
            "收入范围": {
                "最大值": round(df["revenue"].max(), 2),
                "最小值": round(df["revenue"].min(), 2),
                "均值": round(df["revenue"].mean(), 2),
            }
        },
        "evidence": f"数据概览，共{len(df)}行{len(df.columns)}列",
    }

def compare_groups(group_col: str, group_a: str, group_b: str,value_col: str, agg_func: str) -> dict:
    if group_col not in VALUE_COLS:
        return {"error": f"{group_col}不是有效字段"}
    if value_col not in VALUE_COLS:
        return {"error": f"{value_col}不是有效字段"}
    if agg_func not in VALUE_AGG:
        return {"error": f"{agg_func}不是有效聚合函数"}

    filtered_a = df[df[group_col] == group_a]
    filtered_b = df[df[group_col] == group_b]
    if len(filtered_a) == 0:
        return {"error": f"没有找到{group_col}={group_a} 的数据"}
    if len(filtered_b) == 0:
        return {"error": f"没有找到{group_col}={group_b} 的数据"}

    val_a = round(filtered_a[value_col].agg(agg_func), 2)
    val_b = round(filtered_b[value_col].agg(agg_func), 2)

    return {
        "result": {
            group_a: float(val_a),
            group_b: float(val_b),
            "差值": round(float(val_a) - float(val_b), 2),
        },
        "evidence": f"对比 {group_col}={group_a} 和 {group_col}={group_b}, 对{value_col}求{agg_func}"
    }

def detect_anomaly(value_col: str, group_col: str=None, group_val: str=None) -> dict:
    if value_col not in VALUE_COLS:
        return {"error": f"{value_col}不是有效字段"}
    if group_col and group_val:
        filtered = df[df[group_col] == group_val]
        if len(filtered) == 0:
            return {"error": f"没有找到{group_col}={group_val}的数据"}
        Q1 = filtered[value_col].quantile(0.25)
        Q3 = filtered[value_col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 -1.5 * IQR
        upper = Q3 + 1.5 * IQR
        anomalies = filtered[(filtered[value_col] < lower) | (filtered[value_col] > upper)]
    else:
        Q1 = df[value_col].quantile(0.25)
        Q3 = df[value_col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 -1.5 * IQR
        upper = Q3 + 1.5 * IQR
        anomalies = df[(df[value_col] < lower) | (df[value_col] > upper)]

    return {
        "result": {
            "异常行数": len(anomalies),
            "下界": round(float(lower), 2),
            "上界": round(float(upper), 2),
            "异常值均值": round(float(anomalies[value_col].mean()), 2) if len(anomalies) > 0 else None,
        },
        "evidence": f"对{value_col}做IQR异常检测，下界{round(float(lower), 2)}, 上界{round(float(lower), 2)}"
    }
