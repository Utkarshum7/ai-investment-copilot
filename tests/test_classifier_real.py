from src.classifier import classify


def test_real_routing():
    queries = [
        ("how is my portfolio doing", "portfolio_health"),
        ("calculate my returns on 10k investment", "financial_calculator"),
        ("tell me about apple stock", "market_research"),
        ("give me long term investment strategy", "investment_strategy"),
    ]

    correct = 0

    for q, expected in queries:
        result = classify(q, llm=None)  # no mock
        if result.agent == expected:
            correct += 1

    accuracy = correct / len(queries)
    assert accuracy >= 0.75  # your own sanity check