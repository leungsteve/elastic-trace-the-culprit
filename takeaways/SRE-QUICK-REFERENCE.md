# SRE Quick Reference Guide

## Incident Investigation with Elastic Observability

*From the "From Commit to Culprit" Workshop*

---

## The Investigation Workflow

```
ALERT FIRES
    │
    ▼
┌─────────────────┐
│ 1. ACKNOWLEDGE  │  "I see it, I am on it"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. SCOPE        │  "What is affected?"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. INVESTIGATE  │  "What changed?"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. REMEDIATE    │  "How do we fix it?"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. VERIFY       │  "Is it fixed?"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. DOCUMENT     │  "What did we learn?"
└─────────────────┘
```

---

## Quick Navigation in Kibana

| Task | Navigation Path |
|------|-----------------|
| View all services | Observability → APM → Services |
| See service dependencies | Observability → APM → Service Map |
| Check SLO status | Observability → SLOs |
| View active alerts | Observability → Alerts |
| Search logs | Observability → Logs |
| Check infrastructure | Observability → Infrastructure |
| ML anomalies | Machine Learning → Anomaly Explorer |
| Agent Builder | Kibana → Agents |

---

## From Alert to Root Cause

### Step 1: Acknowledge the Alert

**Location:** Observability → Alerts

**Actions:**
- Click the alert to see details
- Note: service name, severity, trigger time
- Click "View in APM" to drill down

### Step 2: Scope the Impact

**In APM Service Overview:**
- Check latency chart: Is it up?
- Check error rate: Are requests failing?
- Check throughput: Is traffic normal?
- Look at the timeline: When did it start?

**In Service Map:**
- Which services are affected?
- Are dependencies healthy?
- Where is the bottleneck?

### Step 3: Use Correlations

**Location:** APM → Service → Correlations tab

**What to look for:**
- Fields with high impact percentage
- Common values in slow/failed requests
- Differences between good and bad requests

**Common high-impact fields:**
- `service.version` (deployment issue)
- `host.name` (infrastructure issue)
- `url.path` (specific endpoint issue)
- `user.id` (user-specific issue)

### Step 4: Examine Traces

**Location:** APM → Traces

**Filter for slow/failed transactions:**
- Click a problematic transaction
- Examine the waterfall view
- Look for: Long spans, errors, gaps

**Span Investigation:**
- Click the slow span
- Check span attributes
- Look for: author, commit, PR metadata

### Step 5: Correlate with Logs

**From a trace:**
- Copy the `trace.id` from trace metadata
- Navigate to Logs
- Add filter: `trace.id: <copied-id>`
- Read logs in chronological order

**Direct log search:**
- Filter by service: `service.name: order-service`
- Filter by level: `log.level: error`
- Look for patterns, stack traces, error messages

---

## SLO Concepts

### Key Terms

| Term | Definition |
|------|------------|
| SLI | Service Level Indicator. The metric being measured. |
| SLO | Service Level Objective. The target for the SLI. |
| Error Budget | How much the SLI can miss the SLO before action is needed. |
| Burn Rate | How fast the error budget is being consumed. |

### Reading SLO Status

| Status | Meaning | Action |
|--------|---------|--------|
| Green (> 90% budget) | Healthy | Continue normal operations |
| Yellow (50-90% budget) | Caution | Investigate trends |
| Red (< 50% budget) | At risk | Prioritize reliability work |
| Burning (> 1x rate) | Active incident | Immediate investigation |

### Burn Rate Thresholds

| Burn Rate | Time to Exhaust Budget | Urgency |
|-----------|------------------------|---------|
| 1x | Full window (e.g., 30 days) | Normal |
| 2x | Half window (e.g., 15 days) | Elevated |
| 6x | ~5 days | High |
| 14x | ~2 days | Critical |

---

## Common Failure Patterns

### Pattern 1: Latency Spike

**Symptoms:**
- Sudden increase in response time
- SLO burn rate increases
- Throughput may remain normal

**Common Causes:**
- Bad deployment (new code)
- Slow dependency
- Database query issue
- Resource contention

**Investigation Path:**
APM → Latency chart → Correlations → Slow traces → Span analysis

### Pattern 2: Error Rate Increase

**Symptoms:**
- Increased 5xx responses
- Error rate SLO burning
- Some requests succeed, others fail

**Common Causes:**
- Bad deployment (exception in code)
- Downstream service failure
- Configuration error
- Resource exhaustion

**Investigation Path:**
APM → Errors tab → Error grouping → Stack traces → Logs

### Pattern 3: Gradual Degradation

**Symptoms:**
- Slow increase in latency over hours
- Memory or CPU climbing
- Periodic latency spikes (GC pauses)

**Common Causes:**
- Memory leak
- Connection pool exhaustion
- Cache not clearing
- Growing queue

**Investigation Path:**
Infrastructure metrics → Resource trends → Correlate with APM → Logs

### Pattern 4: Cascading Failure

**Symptoms:**
- Multiple services affected
- Service map shows multiple red nodes
- Multiple alerts firing

**Common Causes:**
- Core dependency failure
- Database or cache down
- Network partition
- Load spike

**Investigation Path:**
Service map → Find root service → Fix root cause → Watch cascade resolve

---

## Useful Queries

### Log Queries

```
# Errors in a specific service
service.name: "order-service" AND log.level: "error"

# Logs for a specific trace
trace.id: "abc123def456"

# Recent deployments
message: "deployment" OR message: "deploy"

# Exceptions
message: "Exception" OR message: "Error"
```

### KQL for APM

```
# Slow transactions
transaction.duration.us > 2000000

# Failed transactions
transaction.result: "error" OR http.response.status_code >= 500

# Specific version
service.version: "v1.1-bad"

# Specific author (if in metadata)
labels.deployment_author: "jordan.rivera"
```

---

## Agent Builder Prompts

### Incident Investigation

- "What happened in the last hour?"
- "When did the latency start increasing?"
- "What deployments occurred today?"
- "Show me the error rate trend"

### Root Cause Analysis

- "What is different about slow requests?"
- "Compare v1.0 and v1.1 performance"
- "What code changed in the last deployment?"
- "Who deployed order-service v1.1?"

### Business Impact

- "How many orders failed during the incident?"
- "Calculate the revenue impact"
- "How much error budget did we burn?"
- "What is our current SLO status?"

### Post-Incident

- "Create a timeline of the incident"
- "Summarize what happened"
- "What should we do to prevent this?"

---

## Remediation Checklist

### Before Rollback

- [ ] Confirm the problematic version
- [ ] Verify the previous version is stable
- [ ] Check for data migration dependencies
- [ ] Notify stakeholders

### During Rollback

- [ ] Execute rollback command
- [ ] Monitor deployment progress
- [ ] Watch for health check pass
- [ ] Verify traffic is routing correctly

### After Rollback

- [ ] Confirm latency/errors normalized
- [ ] Verify SLO recovering
- [ ] Check alert resolved
- [ ] Communicate recovery to stakeholders

---

## Post-Incident Actions

### Immediate (within 1 hour)

- [ ] Document incident timeline
- [ ] Identify root cause
- [ ] Communicate to stakeholders
- [ ] Create incident ticket/case

### Short-term (within 24 hours)

- [ ] Write preliminary post-mortem
- [ ] Identify contributing factors
- [ ] Create follow-up action items
- [ ] Share learnings with team

### Long-term (within 1 week)

- [ ] Complete blameless post-mortem
- [ ] Implement preventive measures
- [ ] Update runbooks if needed
- [ ] Review detection/response effectiveness

---

## Key Metrics to Monitor

### Service Health

| Metric | Healthy Range | Alert Threshold |
|--------|---------------|-----------------|
| Latency (p95) | < 500ms | > 2000ms |
| Error rate | < 1% | > 5% |
| Throughput | ±20% of baseline | ±50% of baseline |

### Infrastructure

| Metric | Healthy Range | Alert Threshold |
|--------|---------------|-----------------|
| CPU usage | < 70% | > 90% |
| Memory usage | < 80% | > 95% |
| Disk I/O | < 70% | > 90% |

### Business

| Metric | Normal | Action Required |
|--------|--------|-----------------|
| Orders per hour | Baseline ± 10% | < 50% of baseline |
| Payment success | > 99% | < 95% |
| Customer complaints | < 10/hour | > 50/hour |

---

## Resources

- [Elastic Observability Docs](https://www.elastic.co/docs/solutions/observability)
- [APM Guide](https://www.elastic.co/docs/solutions/observability/apm)
- [SLO Documentation](https://www.elastic.co/docs/solutions/observability/incident-management/service-level-objectives-slos)
- [Log Monitoring](https://www.elastic.co/docs/solutions/observability/logs)
- [Workshop Repository](https://github.com/your-org/from-commit-to-culprit)

---

*Remember: Stay calm, follow the data, and document everything.*

*Happy investigating!*
