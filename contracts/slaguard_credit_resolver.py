# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
import typing
from datetime import datetime
from urllib.parse import urlparse

from genlayer import *

NO_CREDIT = "NO_CREDIT"
SERVICE_CREDIT = "SERVICE_CREDIT"
FULL_REFUND = "FULL_REFUND"
NEEDS_REVIEW = "NEEDS_REVIEW"
VALID_DECISIONS = [NO_CREDIT, SERVICE_CREDIT, FULL_REFUND, NEEDS_REVIEW]


class SLAGuardCreditResolver(gl.Contract):
    service_name: str
    sla_policy_url: str
    allowed_domain_one: str
    allowed_domain_two: str
    monthly_fee: u256
    max_evidence_sources: u256
    resolutions: DynArray[str]
    latest_resolution: str

    def __init__(
        self,
        service_name: str,
        sla_policy_url: str,
        allowed_domain_one: str,
        allowed_domain_two: str,
        monthly_fee: int,
        max_evidence_sources: int,
    ):
        service_name = service_name.strip()
        sla_policy_url = sla_policy_url.strip()
        if not service_name:
            raise ValueError("Service name is required.")
        if not sla_policy_url:
            raise ValueError("SLA policy URL is required.")
        if monthly_fee < 0:
            raise ValueError("monthly_fee cannot be negative.")
        if max_evidence_sources < 1 or max_evidence_sources > 3:
            raise ValueError("max_evidence_sources must be between 1 and 3.")

        self.service_name = service_name
        self.sla_policy_url = sla_policy_url
        self.allowed_domain_one = _normalize_domain(allowed_domain_one)
        self.allowed_domain_two = _normalize_domain(allowed_domain_two)
        self.monthly_fee = u256(monthly_fee)
        self.max_evidence_sources = u256(max_evidence_sources)
        self.latest_resolution = ""

    @gl.public.write
    def resolve_credit(
        self,
        account_id: str,
        incident_window: str,
        customer_claim: str,
        evidence_url_one: str,
        evidence_url_two: str,
        evidence_url_three: str,
    ) -> typing.Any:
        account_id = account_id.strip()
        incident_window = incident_window.strip()
        customer_claim = customer_claim.strip()
        if not account_id:
            raise ValueError("Account ID is required.")
        if not incident_window:
            raise ValueError("Incident window is required.")
        if not customer_claim:
            raise ValueError("Customer claim is required.")

        evidence_urls = self._collect_evidence_urls(
            evidence_url_one, evidence_url_two, evidence_url_three
        )
        service_name = self.service_name
        sla_policy_url = self.sla_policy_url
        monthly_fee = int(self.monthly_fee)

        def evaluate_credit() -> str:
            sla_policy_text = gl.get_webpage(sla_policy_url, mode="text")
            evidence_bundle = []
            for evidence_url in evidence_urls:
                evidence_bundle.append(
                    {
                        "url": evidence_url,
                        "text": gl.get_webpage(evidence_url, mode="text"),
                    }
                )

            task = f"""
You are resolving a service credit claim under an SLA policy.

Service:
{service_name}

SLA policy URL:
{sla_policy_url}

SLA policy text:
{sla_policy_text}

Account ID:
{account_id}

Incident window:
{incident_window}

Customer claim:
{customer_claim}

Monthly fee:
{monthly_fee}

Evidence bundle:
{json.dumps(evidence_bundle, sort_keys=True)}

Return only valid JSON with this exact schema:
{{
  "account_id": "{account_id}",
  "decision": "NO_CREDIT | SERVICE_CREDIT | FULL_REFUND | NEEDS_REVIEW",
  "credit_percent": 0,
  "estimated_downtime_minutes": 0,
  "confidence": 0,
  "sla_basis": ["short policy clauses or SLA facts used"],
  "evidence_basis": ["short incident or status facts used"],
  "reasoning": "brief explanation"
}}

Rules:
- NO_CREDIT means the policy and evidence do not support a credit.
- SERVICE_CREDIT means the policy supports a partial credit.
- FULL_REFUND means the policy supports a full monthly refund.
- NEEDS_REVIEW means the evidence is missing, contradictory, or not settled by the SLA.
- credit_percent must be 0 to 100.
- estimated_downtime_minutes must be 0 or greater.
- confidence must be 0 to 100.
- Do not include markdown, prose, or extra keys.
            """
            result = gl.exec_prompt(task)
            result_dict = _parse_json_dict(result)
            _validate_resolution(result_dict)
            return _canonical_json(result_dict)

        agreed_result = gl.eq_principle_prompt_comparative(
            evaluate_credit,
            principle=(
                "The `decision`, `credit_percent`, `estimated_downtime_minutes`, and `account_id` fields must match. "
                "SLA basis and evidence basis must support the same outcome."
            ),
        )
        resolution = _parse_json_dict(agreed_result)
        credit_amount = (monthly_fee * resolution["credit_percent"]) // 100

        record = {
            "id": len(self.resolutions) + 1,
            "submitter": gl.message.sender_address.as_hex,
            "service_name": service_name,
            "sla_policy_url": sla_policy_url,
            "account_id": account_id,
            "incident_window": incident_window,
            "customer_claim": customer_claim,
            "evidence_urls": evidence_urls,
            "monthly_fee": monthly_fee,
            "credit_amount": credit_amount,
            "resolution": resolution,
            "created_at": datetime.now().astimezone().isoformat(),
        }
        record_json = _canonical_json(record)
        self.resolutions.append(record_json)
        self.latest_resolution = record_json
        return record

    def _collect_evidence_urls(
        self, evidence_url_one: str, evidence_url_two: str, evidence_url_three: str
    ) -> list[str]:
        evidence_urls = []
        for evidence_url in [evidence_url_one, evidence_url_two, evidence_url_three]:
            evidence_url = evidence_url.strip()
            if not evidence_url:
                continue
            if len(evidence_urls) >= self.max_evidence_sources:
                raise ValueError("Too many evidence URLs.")
            if not self._domain_allowed(evidence_url):
                raise ValueError("Evidence URL domain is not allowed.")
            if evidence_url not in evidence_urls:
                evidence_urls.append(evidence_url)
        if len(evidence_urls) == 0:
            raise ValueError("At least one evidence URL is required.")
        return evidence_urls

    def _domain_allowed(self, evidence_url: str) -> bool:
        domain = _normalize_domain(evidence_url)
        return domain in [self.allowed_domain_one, self.allowed_domain_two]

    @gl.public.view
    def get_config(self) -> dict:
        return {
            "service_name": self.service_name,
            "sla_policy_url": self.sla_policy_url,
            "allowed_domain_one": self.allowed_domain_one,
            "allowed_domain_two": self.allowed_domain_two,
            "monthly_fee": self.monthly_fee,
            "max_evidence_sources": self.max_evidence_sources,
        }

    @gl.public.view
    def get_resolution_count(self) -> int:
        return len(self.resolutions)

    @gl.public.view
    def get_latest_resolution(self) -> typing.Any:
        if not self.latest_resolution:
            return {}
        return json.loads(self.latest_resolution)

    @gl.public.view
    def get_resolution(self, resolution_id: int) -> typing.Any:
        if resolution_id < 1 or resolution_id > len(self.resolutions):
            raise ValueError("Resolution not found.")
        return json.loads(self.resolutions[resolution_id - 1])


def _normalize_domain(value: str) -> str:
    value = value.strip().lower()
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    return parsed.netloc.replace("www.", "").split(":")[0]


def _parse_json_dict(json_str: str) -> dict:
    first_brace = json_str.find("{")
    last_brace = json_str.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
        raise ValueError("No JSON object found.")
    return json.loads(json_str[first_brace : last_brace + 1])


def _canonical_json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _validate_resolution(value: dict) -> None:
    if value.get("decision") not in VALID_DECISIONS:
        raise ValueError("Invalid SLA decision.")
    credit_percent = value.get("credit_percent")
    if (
        not isinstance(credit_percent, int)
        or credit_percent < 0
        or credit_percent > 100
    ):
        raise ValueError("Invalid credit percent.")
    downtime = value.get("estimated_downtime_minutes")
    if not isinstance(downtime, int) or downtime < 0:
        raise ValueError("Invalid downtime.")
    confidence = value.get("confidence")
    if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
        raise ValueError("Invalid confidence.")
    for field in ["sla_basis", "evidence_basis"]:
        if not isinstance(value.get(field), list):
            raise ValueError(f"{field} must be a list.")
