"""
Data Analysis Tool — CSV/DataFrame analysis using pandas.
"""
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def analyze_csv(filepath: str) -> str:
    """
    Perform statistical analysis on a CSV file.
    Returns a JSON string with summary statistics and detected trends.
    """
    try:
        import pandas as pd

        df = pd.read_csv(filepath)
        results: Dict[str, Any] = {
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": df.isnull().sum().to_dict(),
            "numeric_summary": {},
            "trends": [],
        }

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            desc = df[numeric_cols].describe()
            results["numeric_summary"] = desc.to_dict()

            # Simple trend detection: compare first/last quarter means
            for col in numeric_cols[:5]:  # limit to 5 columns
                try:
                    q = len(df) // 4
                    if q > 0:
                        first_mean = float(df[col].iloc[:q].mean())
                        last_mean = float(df[col].iloc[-q:].mean())
                        pct_change = ((last_mean - first_mean) / (abs(first_mean) + 1e-9)) * 100
                        direction = "increasing" if pct_change > 5 else "decreasing" if pct_change < -5 else "stable"
                        results["trends"].append({
                            "column": col,
                            "direction": direction,
                            "pct_change": round(pct_change, 2),
                        })
                except Exception:
                    pass

        return json.dumps(results, indent=2, default=str)
    except ImportError:
        return '{"error": "pandas not installed"}'
    except Exception as e:
        logger.error(f"[DataAnalysis] CSV analysis failed for {filepath}: {e}")
        return json.dumps({"error": str(e)})


def summarize_dataframe_text(analysis_json: str) -> str:
    """Convert pandas analysis JSON to a human-readable summary for the LLM."""
    try:
        data = json.loads(analysis_json)
        lines = [
            f"Dataset: {data['shape']['rows']} rows × {data['shape']['columns']} columns",
            f"Columns: {', '.join(data['columns'][:10])}",
        ]
        if data.get("trends"):
            lines.append("\nDetected Trends:")
            for t in data["trends"]:
                lines.append(f"  - {t['column']}: {t['direction']} ({t['pct_change']:+.1f}%)")
        missing = {k: v for k, v in data.get("missing_values", {}).items() if v > 0}
        if missing:
            lines.append(f"\nMissing Values: {missing}")
        return "\n".join(lines)
    except Exception:
        return analysis_json
