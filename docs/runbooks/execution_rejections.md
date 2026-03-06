# Execution Rejections

Symptoms:

- High `ExecutionRejectedRateHigh` alert firing.

Immediate actions:

- Check the execution service logs for rejection reasons.
- Verify risk limits and operator interventions.
- If caused by downstream exchange, check exchange backoff and connectivity.

Escalation:

- Contact on-call trading operator.
