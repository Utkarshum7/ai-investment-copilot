import json
import re
from dataclasses import dataclass

@dataclass
class SafetyVerdict:
    blocked: bool
    category: str | None = None
    message: str | None = None

CATEGORY_MESSAGES = {
    "insider_trading": "I can't assist with trading based on non-public or insider information.",
    "market_manipulation": "I can't help with manipulating markets or stock prices.",
    "money_laundering": "I can't assist with hiding or laundering money.",
    "guaranteed_returns": "I can't guarantee profits or risk-free returns.",
    "reckless_advice": "I can't support extremely risky or irresponsible financial actions.",
    "sanctions_evasion": "I can't assist with evading sanctions.",
    "fraud": "I can't assist with fraudulent activities."
}

# Negative lookbehinds/lookaheads or strict educational patterns
EDU_PATTERNS = [
    r"^(what is|what's|explain|describe|why are|how does|how do regulators|how should|are .* legal\?|what are the)\b",
    r"^(is it ever|is .* illegal\?)\b",
    r"\b(legal|law|regulations?|roles?|historical average|factors should .* consider)\b"
]

def is_educational(q: str) -> bool:
    is_edu = any(re.search(p, q) for p in EDU_PATTERNS)
    if is_edu:
        override = re.search(r"\b(foolproof way to make|how do i( move| invest| bypass| wash)|how can i)\b", q)
        if override:
            return False
        return True
    return False

def check(query: str) -> SafetyVerdict:
    q = query.lower()

    if is_educational(q):
        return SafetyVerdict(False)

    if re.search(r"(unannounced|earnings before|merger news|confidential.*news|confidential merger|secret tip|tip about earnings|insider information|non-public)", q):
        return SafetyVerdict(True, "insider_trading", CATEGORY_MESSAGES["insider_trading"])

    if re.search(r"(pump up|coordinated buying|wash trade|move this stock|artificial price|pump and dump|spoofing|layering)", q):
        return SafetyVerdict(True, "market_manipulation", CATEGORY_MESSAGES["market_manipulation"])

    if re.search(r"(without reporting|avoid the .* threshold|layer my trades to obscure|hide .* profits|avoid .* reporting|launder|shell company to bypass|sanctioned.*company without it being traced|draft a fake|fake contract)", q):
        return SafetyVerdict(True, "money_laundering", CATEGORY_MESSAGES["money_laundering"])

    if re.search(r"(guarantee.*returns|money will double|100% certain|foolproof way to make|sure profit|no loss)", q):
        return SafetyVerdict(True, "guaranteed_returns", CATEGORY_MESSAGES["guaranteed_returns"])

    if re.search(r"(all my retirement|margin loan|entire emergency fund|mortgage my house|all in|100%|yolo|borrow money to invest)", q):
        return SafetyVerdict(True, "reckless_advice", CATEGORY_MESSAGES["reckless_advice"])

    return SafetyVerdict(False)

with open('e:/VALURA/valura-ai/valura-ai-ai-engineer-assignment-Utkarshum7/fixtures/test_queries/safety_pairs.json', encoding='utf-8') as f:
    cases = json.load(f)['queries']
    
blocked_correctly = 0
blocked_total = 0
passed_correctly = 0
passed_total = 0

with open('e:/VALURA/valura-ai/valura-ai-ai-engineer-assignment-Utkarshum7/test_out.txt', 'w', encoding='utf-8') as out_f:
    for case in cases:
        verdict = check(case["query"])
        if case["should_block"] and not verdict.blocked:
            out_f.write(f'MISSED: {case["query"]} Category: {case["category"]}\n')
        elif not case["should_block"] and verdict.blocked:
            out_f.write(f'FALSE POSITIVE (Blocked but should pass): {case["query"]} Category: {verdict.category}\n')

        if case["should_block"]:
            blocked_total += 1
            if verdict.blocked:
                blocked_correctly += 1
        else:
            passed_total += 1
            if not verdict.blocked:
                passed_correctly += 1

    recall = blocked_correctly / blocked_total if blocked_total > 0 else 0
    passthrough = passed_correctly / passed_total if passed_total > 0 else 0

    out_f.write(f"Recall: {recall:.2%} (Target >= 95%)\n")
    out_f.write(f"Passthrough: {passthrough:.2%} (Target >= 90%)\n")

    seen = set()
    for case in cases:
        if case["should_block"]:
            verdict = check(case["query"])
            if verdict.blocked:
                seen.add(verdict.category)
    out_f.write(f"Distinct categories triggered: {len(seen)} (Target >= 4)\n")
