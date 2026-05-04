from typing import Dict, Any


def run(user: Dict[str, Any], llm=None) -> Dict[str, Any]:
    user = user or {}
    # ---- Extract positions safely ----
    positions = []

    # case 1: holdings
    holdings = user.get("holdings")
    if isinstance(holdings, list):
        positions = holdings

    # case 2: portfolio.positions
    elif isinstance(user.get("portfolio"), dict):
        portfolio = user.get("portfolio", {})
        if isinstance(portfolio.get("positions"), list):
            positions = portfolio.get("positions", [])

    # case 3: root positions
    elif isinstance(user.get("positions"), list):
        positions = user.get("positions", [])

    # ---- Normalize values ----
    cleaned_positions = []
    for p in positions:
        try:
            value = None
            if p.get("current_value") is not None:
                value = float(p.get("current_value"))
            elif p.get("value") is not None:
                value = float(p.get("value"))
            elif p.get("quantity") is not None and p.get("avg_cost") is not None:
                value = float(p.get("quantity")) * float(p.get("avg_cost"))
            
            if value is not None and value > 0:
                cleaned_positions.append({"value": value})
        except (TypeError, ValueError):
            continue

    # ---- EMPTY CASE ----
    if not cleaned_positions:
        return {
            "concentration_risk": {
                "top_position_pct": 0,
                "top_3_positions_pct": 0,
                "flag": "none",
            },
            "performance": {
                "total_return_pct": 0,
                "annualized_return_pct": 0,
            },
            "benchmark_comparison": {
                "benchmark": "S&P 500",
                "portfolio_return_pct": 0,
                "benchmark_return_pct": 0,
                "alpha_pct": 0,
            },
            "observations": [
                {
                    "severity": "info",
                    "text": "You don't have a portfolio yet. Consider starting with a diversified set of assets aligned to your goals.",
                }
            ],
            "disclaimer": "This is not investment advice. Please consult a financial advisor.",
        }

    # ---- Calculations ----
    total_value = sum(p["value"] for p in cleaned_positions)

    sorted_positions = sorted(
        cleaned_positions,
        key=lambda x: x["value"],
        reverse=True
    )

    top_position_pct = (sorted_positions[0]["value"] / total_value) * 100

    top_3_value = sum(p["value"] for p in sorted_positions[:3])
    top_3_positions_pct = (top_3_value / total_value) * 100

    # ---- Flag ----
    if top_position_pct >= 50:
        flag = "high"
    elif top_position_pct >= 30:
        flag = "warning"
    else:
        flag = "none"

    # ---- Mock performance ----
    total_return_pct = 10.0
    annualized_return_pct = 7.0

    country = user.get("country")
    if country and country != "US":
        benchmark = "MSCI World"
    else:
        benchmark = "S&P 500"

    benchmark_return = 8.0
    alpha = total_return_pct - benchmark_return

    # ---- Observations ----
    observations = []

    if flag in {"high", "warning"}:
        observations.append({
            "severity": "warning",
            "text": f"{round(top_position_pct,1)}% of your portfolio is concentrated in a single asset."
        })

    performance_verb = "beating" if alpha > 0 else "trailing"
    observations.append({
        "severity": "info",
        "text": f"Your portfolio's growth is {performance_verb} the market average ({benchmark}) by {round(abs(alpha),1)}%."
    })

    return {
        "concentration_risk": {
            "top_position_pct": round(top_position_pct, 1),
            "top_3_positions_pct": round(top_3_positions_pct, 1),
            "flag": flag,
        },
        "performance": {
            "total_return_pct": total_return_pct,
            "annualized_return_pct": annualized_return_pct,
        },
        "benchmark_comparison": {
            "benchmark": benchmark,
            "portfolio_return_pct": total_return_pct,
            "benchmark_return_pct": benchmark_return,
            "alpha_pct": round(alpha, 1),
        },
        "observations": observations,
        "disclaimer": "This is not investment advice. Please consult a financial advisor.",
    }