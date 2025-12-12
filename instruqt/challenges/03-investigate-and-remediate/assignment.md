---
slug: 03-investigate-and-remediate
id: 03-investigate-and-remediate
type: challenge
title: "Investigate and Remediate"
teaser: "Find the smoking gun and watch automated remediation"
---

# Investigate and Remediate

> The alert is clear: Order Service latency has spiked. Customers are complaining on social media. Sam Patel pings you on Slack: "Alex, what is happening? Can you get this resolved before the weekend rush?"
>
> You take a deep breath. Time to find the culprit.

## Your Mission

In this challenge, you will:

1. Use APM Correlations to identify what is different about slow requests
2. Drill down into a slow trace to find the root cause
3. Use span attributes to identify the author and commit
4. Correlate traces with logs to see the problematic code
5. Observe automated rollback triggered by the Workflow
6. Verify system recovery

## Step 1: Navigate from Alert to Investigation

Go to **Observability > Alerts** in Kibana.

Find the **Order Service SLO Burn Rate** alert (should be active/firing).

Click on the alert, then click **View in APM** or navigate manually to **Observability > APM > Services > order-service**.

## Step 2: Use APM Correlations

In the Order Service page, look for the **Correlations** tab or panel.

APM Correlations uses statistical analysis to identify attributes that are highly correlated with slow requests. This feature automatically highlights what is different about problematic requests.

You should see a correlation like:

```
Field: service.version
Value: v1.1-bad
Impact: 94% correlation with high latency
```

This tells us that requests handled by version `v1.1-bad` are highly correlated with slow performance.

Click on the correlation to filter transactions to only those affected by this version.

## Step 3: Examine a Slow Trace

Navigate to **Observability > APM > Traces** (or click from the service page).

Apply filters:
- **service.name:** order-service
- **service.version:** v1.1-bad

You should see traces with duration around 2000-2300ms (compared to the baseline of 100-300ms).

Click on one of the slowest traces to open the trace waterfall view.

## Step 4: Find the Smoking Gun Span

In the trace waterfall, you will see the flow of the request across services:

```
order-service
├── POST /api/orders (~2100ms total)
    ├── detailed-trace-logging (2001ms) ← THIS IS THE PROBLEM
    ├── inventory-service
    │   └── POST /api/inventory/check (~30ms)
    ├── inventory-service
    │   └── POST /api/inventory/reserve (~30ms)
    └── payment-service
        └── POST /api/payments (~40ms)
```

Notice the **detailed-trace-logging** span taking approximately 2000ms. This span is new and was not present in the v1.0 traces.

Click on the **detailed-trace-logging** span to view its details.

## Step 5: Examine Span Attributes

In the span detail panel on the right, expand the **Metadata** or **Attributes** section.

You should see custom attributes added by the developer:

```yaml
logging.type: "detailed-trace"
logging.author: "jordan.rivera"
logging.commit_sha: "a1b2c3d4"
logging.pr_number: "PR-1247"
logging.delay_ms: 2000
logging.destination: "/var/log/orders/trace.log"
```

**Aha!** The span attributes tell us:
- Who wrote this code: **jordan.rivera**
- Which commit introduced it: **a1b2c3d4**
- What it is doing: Writing detailed trace logs to disk
- How long it takes: **2000ms** per request

This is the root cause. Jordan added synchronous file I/O that blocks every request for 2 seconds.

## Step 6: Correlate with Logs

Copy the **trace.id** from the trace metadata.

Navigate to **Observability > Logs > Stream** and add a filter:

```
trace.id: <paste-the-trace-id>
```

Look for a log message from order-service. You should see something like:

```
2024-01-15 14:48:23.456 DEBUG [abc123...] Writing detailed trace data to disk: 2000ms [OrderController.java:47]
```

Notice:
- The log includes the trace ID (log correlation)
- The message describes the 2000ms delay
- The file and line number are included: `OrderController.java:47`

You have now traced the problem from alert to the exact line of code.

## Step 7: Observe Automated Rollback

While you have been investigating, the SLO burn rate alert has triggered an **Elastic Workflow**.

The Workflow is configured to:
1. Detect when SLO burn rate exceeds 6x sustainable rate
2. Send a webhook to the rollback service
3. Trigger an automated rollback to the previous version (v1.0)

Navigate to **Management > Rules** to see the rule configuration.

### Watch for Rollback

Monitor the terminal or run:

```bash
cd /root/from-commit-to-culprit
docker compose -f infra/docker-compose.yml logs -f order-service
```

You should see the order-service container restart as it rolls back to v1.0.

Alternatively, check the current version:

```bash
grep ORDER_SERVICE_VERSION /root/from-commit-to-culprit/infra/.env
```

After the rollback, it should show `v1.0`.

## Step 8: Verify System Recovery

After the rollback (within 2-3 minutes):

### Check APM Latency

Navigate to **Observability > APM > Services > order-service**.

Watch the latency chart. You should see:
- A period of high latency (~2000ms) during the v1.1-bad deployment
- A sharp drop back to baseline (~100-300ms) after rollback

### Check SLO Status

Navigate to **Observability > SLOs**.

The **Order Service - Latency P95 < 500ms** SLO should:
- Show improving SLI percentage
- Burn rate returning to normal levels
- Status transitioning from red/yellow back to green

### Check Alert Status

Navigate to **Observability > Alerts**.

The **Order Service SLO Burn Rate** alert should transition to:
- **Status:** Recovered
- **Last alert:** Shows when it fired
- **Duration:** Shows how long the incident lasted

## Step 9: Note the Impact

Before moving on, take note of the approximate incident duration and impact:

- **Incident start:** When you deployed v1.1-bad
- **Incident end:** When the rollback completed
- **Duration:** Approximately how many minutes

In Challenge 4, you will use Agent Builder to calculate the exact business impact and create a Case for documentation.

## Checkpoint

Before moving to the next challenge, verify:

- [ ] Used APM Correlations to identify service.version as the culprit
- [ ] Found the detailed-trace-logging span in a slow trace
- [ ] Identified Jordan Rivera as the author via span attributes
- [ ] Correlated trace with logs to see the delay message
- [ ] Observed automated rollback to v1.0
- [ ] Verified latency returned to baseline
- [ ] Confirmed SLO status improved and alert recovered

## What You Learned

In this challenge, you:
- Used APM Correlations to statistically identify the problem attribute
- Drilled down from alert to service to trace to span
- Leveraged custom span attributes for root cause attribution
- Used trace-to-log correlation to see detailed code behavior
- Observed Elastic Workflows triggering automated remediation
- Verified system recovery after rollback
- Calculated business impact for stakeholder reporting

The incident is resolved, but the investigation is not complete. Time to document what happened and prevent recurrence.

---

**Pro Tip:** The entire investigation from alert to root cause took only minutes because of:
1. **Trace-to-log correlation** (no manual searching)
2. **APM Correlations** (automatic anomaly detection)
3. **Custom span attributes** (developer-added context)
4. **Automated remediation** (Workflows reduced MTTR)

This is modern observability in action.
