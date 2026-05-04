from dataclasses import dataclass
import re
from typing import Any


@dataclass
class ClassificationResult:
    agent: str
    entities: dict[str, Any]
    intent: str = "unknown"


# ---------------------------
# Simple entity extraction
# ---------------------------
def extract_entities(query: str) -> dict:
    q = query.lower()

    entities = {}

    # ---- tickers (basic heuristic: uppercase words like AAPL, NVDA) ----
    tickers = re.findall(r"\b[A-Z]{2,5}\b", query)
    if tickers:
        entities["tickers"] = tickers

    # ---- amount ----
    amt_match = re.search(r"(\d+(?:\.\d+)?)\s*(k|m|lakh|crore)?", q)
    if amt_match:
        try:
            value = float(amt_match.group(1))
            multiplier = amt_match.group(2)

            if multiplier == "k":
                value *= 1_000
            elif multiplier == "m":
                value *= 1_000_000
            elif multiplier == "lakh":
                value *= 100_000
            elif multiplier == "crore":
                value *= 10_000_000

            entities["amount"] = value
        except (ValueError, TypeError):
            pass

    # ---- action ----
    if "buy" in q:
        entities["action"] = "buy"
    elif "sell" in q:
        entities["action"] = "sell"
    elif "hold" in q:
        entities["action"] = "hold"

    # ---- topics ----
    topics = []
    if "crypto" in q:
        topics.append("crypto")
    if "stocks" in q:
        topics.append("stocks")
    if "portfolio" in q:
        topics.append("portfolio")

    if topics:
        entities["topics"] = topics

    return entities


# ---------------------------
# Rule-based routing
# ---------------------------
def route(query: str) -> str:
    q = query.lower()

    # ---- portfolio health (high priority) ----
    if any(word in q for word in [
        "portfolio", "diversified", "diversification", "risk", "health", "allocation"
    ]):
        return "portfolio_health"

    # ---- calculator ----
    if any(word in q for word in [
        "calculate", "roi", "returns", "profit", "compound", "interest"
    ]):
        return "financial_calculator"

    # ---- market research ----
    if any(word in q for word in [
        "tell me about", "analyze", "analysis", "overview", "stock", "company"
    ]):
        return "market_research"

    # ---- investment strategy ----
    if any(word in q for word in [
        "strategy", "plan", "long term", "short term", "invest for", "goal"
    ]):
        return "investment_strategy"

    return "unknown"


# ---------------------------
# MAIN FUNCTION
# ---------------------------
def classify(query: str, history: list = None, llm=None) -> ClassificationResult:
    """
    Must:
    - Work with mock_llm in tests
    - Not crash if LLM fails
    """

    # ✅ If mock_llm provided → use it
    if llm:
        try:
            result = llm()
            agent_str = result.get("agent", "unknown")
            return ClassificationResult(
                agent=agent_str,
                intent=agent_str,
                entities=result.get("entities", {}),
            )
        except Exception:
            pass  # fallback below

    # ✅ fallback: rule-based
    agent = route(query)
    entities = extract_entities(query)
    
    if not entities and history:
        for msg in reversed(history):
            if msg.get("role") == "user":
                past_entities = extract_entities(msg.get("content", ""))
                if past_entities:
                    entities = past_entities
                    break

    return ClassificationResult(agent=agent, intent=agent, entities=entities)