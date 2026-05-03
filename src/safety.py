from dataclasses import dataclass
import re


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
}


# -------- Educational detection --------
EDU_PATTERNS = [
    r"^(what is|what's|explain|describe|why are|how does|how do regulators|how should|are .* legal\?|what are the)\b",
    r"^(is it ever|is .* illegal\?)\b",
    r"\b(legal|law|regulations?|roles?|historical average|factors should .* consider)\b"
]

def is_educational(q: str) -> bool:
    is_edu = any(re.search(p, q) for p in EDU_PATTERNS)
    if is_edu:
        # Override educational classification if extreme directives or first-person harmful actions are detected
        override = re.search(r"\b(foolproof way to make|how do i( move| invest| bypass| wash)|how can i)\b", q)
        if override:
            return False
        return True
    return False


# -------- Main safety check --------
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