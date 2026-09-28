# SLAGuard Credit Resolver

SLAGuard Credit Resolver is a standalone GenLayer Intelligent Contract for resolving service credit claims under a public SLA. It evaluates a customer claim and incident evidence against an SLA policy, reaches validator consensus on the credit decision, and stores a durable resolution on-chain.

The primitive is useful for API providers, SaaS tools, RPC providers, hosting platforms, oracle services, and marketplaces that need transparent service-credit decisions from public incident and status evidence.

## Why GenLayer

SLA resolution often depends on natural-language policies and web evidence such as status pages, incident reports, support updates, or public postmortems. GenLayer validators can fetch these sources, reason over them, and agree on a structured resolution.

The contract uses `gl.get_webpage`, `gl.exec_prompt`, and `gl.eq_principle_prompt_comparative`. Validators must agree on `decision`, `credit_percent`, `estimated_downtime_minutes`, and `account_id`. Reasoning and evidence basis can vary slightly if they support the same outcome.

## Decisions

- `NO_CREDIT`: policy and evidence do not support a credit.
- `SERVICE_CREDIT`: policy supports a partial service credit.
- `FULL_REFUND`: policy supports a full monthly refund.
- `NEEDS_REVIEW`: evidence is missing, contradictory, or not settled by the SLA.

## State Design

- `service_name`: service or provider context.
- `sla_policy_url`: canonical public SLA policy.
- `allowed_domain_one/two`: incident evidence domain allowlist.
- `monthly_fee`: fee basis for credit amount calculation.
- `max_evidence_sources`: bounded evidence count.
- `resolutions`: append-only canonical JSON resolution history.
- `latest_resolution`: cached latest resolution.

## Example Deploy Inputs

```text
service_name: Demo API Service
sla_policy_url: https://github.com/burak33bb/slaguard-credit-resolver/blob/main/README.md
allowed_domain_one: github.com
allowed_domain_two: docs.genlayer.com
monthly_fee: 1000
max_evidence_sources: 3
```

## Example Write Inputs

```text
account_id: ACCT-1001
incident_window: 2026-09-20 10:00 UTC to 2026-09-20 12:00 UTC
customer_claim: API availability fell below the SLA during the incident window.
evidence_url_one: https://github.com/burak33bb/slaguard-credit-resolver
evidence_url_two:
evidence_url_three:
```

## Files

- `contracts/slaguard_credit_resolver.py`: standalone Intelligent Contract source.
- `tests/test_slaguard_credit_resolver.py`: lightweight tests for helper behavior and contract structure.
- `SUBMISSION.md`: short contribution summary.
