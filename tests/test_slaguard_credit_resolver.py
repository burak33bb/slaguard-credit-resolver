import ast
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "slaguard_credit_resolver.py"
CONTRACT_SOURCE = CONTRACT_PATH.read_text(encoding="utf-8")


def normalize_domain(value: str) -> str:
    value = value.strip().lower()
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    return parsed.netloc.replace("www.", "").split(":")[0]


def parse_json_dict(json_str: str) -> dict:
    first_brace = json_str.find("{")
    last_brace = json_str.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
        raise ValueError("No JSON object found.")
    return json.loads(json_str[first_brace : last_brace + 1])


def canonical_json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_normalize_domain_accepts_domains_and_urls():
    assert normalize_domain("www.Example.com") == "example.com"
    assert normalize_domain("https://docs.genlayer.com/path") == "docs.genlayer.com"
    assert normalize_domain("https://example.com:443/path") == "example.com"


def test_parse_json_dict_ignores_wrappers():
    parsed = parse_json_dict(
        '```json\n{"decision":"SERVICE_CREDIT","credit_percent":25}\n```'
    )

    assert parsed == {"decision": "SERVICE_CREDIT", "credit_percent": 25}


def test_canonical_json_is_stable():
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_contract_uses_consensus_and_web_sources():
    assert "gl.eq_principle_prompt_comparative" in CONTRACT_SOURCE
    assert "gl.get_webpage" in CONTRACT_SOURCE
    assert "self.resolutions.append" in CONTRACT_SOURCE


def test_contract_defines_expected_decisions():
    ast.parse(CONTRACT_SOURCE)

    for decision in ["NO_CREDIT", "SERVICE_CREDIT", "FULL_REFUND", "NEEDS_REVIEW"]:
        assert decision in CONTRACT_SOURCE


def test_readme_documents_consensus_and_state():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert re.search(r"Why GenLayer", readme)
    assert "State Design" in readme
    assert "gl.eq_principle_prompt_comparative" in readme
