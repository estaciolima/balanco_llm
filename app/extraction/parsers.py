from decimal import Decimal, InvalidOperation
import re


NUMBER_PATTERN = re.compile(r"-?\d[\d\.,]*")
ACCOUNT_LINE_PATTERN = re.compile(
    r"^\s*(?P<code>\d+(?:\.\d+)*)\s+"
    r"(?P<label>.+?)\s+"
    r"(?P<value>-?\d[\d\.,]*)\s*"
    r"(?P<nature>[DC])?\s*$",
    re.IGNORECASE,
)


def parse_candidate_lines(text_rows: list[dict], reporting_period=None, currency: str = "BRL") -> list[dict]:
    candidates = []
    for row in text_rows:
        for line in row.get("text", "").splitlines():
            account_match = ACCOUNT_LINE_PATTERN.match(line)
            if account_match:
                account_code = account_match.group("code")
                raw_value = account_match.group("value")
                normalized_value = normalize_decimal(raw_value)
                if normalized_value is None:
                    continue
                candidates.append(
                    {
                        "source_account_code": account_code,
                        "source_parent_account_code": derive_parent_account_code(account_code),
                        "source_hierarchy_level": derive_hierarchy_level(account_code),
                        "source_balance_nature": (account_match.group("nature") or "").upper(),
                        "source_label": account_match.group("label").strip(),
                        "raw_value": raw_value,
                        "normalized_value": normalized_value,
                        "currency": currency,
                        "reporting_period": reporting_period,
                        "confidence": 0.82,
                        "evidence": {**row, "source_account_code": account_code},
                    }
                )
                continue

            match = NUMBER_PATTERN.search(line)
            if not match:
                continue
            raw_value = match.group(0)
            label = line[: match.start()].strip(" :-\t")
            normalized_value = normalize_decimal(raw_value)
            if label and normalized_value is not None:
                candidates.append(
                    {
                        "source_account_code": "",
                        "source_parent_account_code": "",
                        "source_hierarchy_level": 0,
                        "source_balance_nature": "",
                        "source_label": label,
                        "raw_value": raw_value,
                        "normalized_value": normalized_value,
                        "currency": currency,
                        "reporting_period": reporting_period,
                        "confidence": 0.7,
                        "evidence": row,
                    }
                )
    return candidates


def normalize_decimal(raw_value: str):
    compact = raw_value.replace(".", "").replace(",", ".")
    try:
        return Decimal(compact)
    except InvalidOperation:
        return None


def derive_parent_account_code(account_code: str) -> str:
    parts = account_code.split(".")
    if len(parts) <= 1:
        return ""
    return ".".join(parts[:-1])


def derive_hierarchy_level(account_code: str) -> int:
    if not account_code:
        return 0
    return len(account_code.split("."))
