# SLAGuard Credit Resolver

## Category

Intelligent Contracts

## Summary

SLAGuard Credit Resolver is a reusable GenLayer Intelligent Contract for service credit claims under a public SLA. A user submits an account ID, incident window, customer claim, and up to three evidence URLs. Validators fetch the SLA policy and incident evidence, evaluate credit eligibility, and store a canonical on-chain resolution.

## Why It Matters

SaaS, API, hosting, RPC, oracle, and marketplace services often need transparent SLA decisions. This contract gives builders a reusable primitive for resolving credits from public policy and incident evidence.

## How Consensus Is Used

The contract uses GenLayer validators with `gl.get_webpage`, `gl.exec_prompt`, and `gl.eq_principle_prompt_comparative`.

Validators must agree on:

- `decision`
- `credit_percent`
- `estimated_downtime_minutes`
- `account_id`

SLA basis, evidence basis, and reasoning may vary slightly, but must support the same result.

## State

- `service_name`: service context.
- `sla_policy_url`: canonical public policy.
- `allowed_domain_one/two`: evidence domain allowlist.
- `monthly_fee`: fee basis for credit calculation.
- `max_evidence_sources`: bounded validator workload.
- `resolutions`: append-only JSON history.
- `latest_resolution`: cached latest result.

## Files

- `contracts/slaguard_credit_resolver.py`
- `README.md`
- `tests/test_slaguard_credit_resolver.py`

## Tests

```text
python -m pytest tests
python -m black --check contracts\slaguard_credit_resolver.py tests\test_slaguard_credit_resolver.py
```
