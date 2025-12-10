# Bonus Challenges

## From Commit to Culprit: Extended Scenarios

**Version:** 1.0
**Last Updated:** December 2024
**Author:** Solutions Architecture Team

---

## Overview

These bonus challenges extend the workshop for participants who want deeper exploration or have additional time. Each bonus challenge introduces a different failure mode and detection pattern, reinforcing the observability concepts from the main workshop.

---

## Bonus Challenge A: The Silent Failure

**Difficulty:** Intermediate
**Duration:** 20-30 minutes
**Focus:** Error rate detection, log pattern analysis

### Scenario

> *It is Saturday morning. The Order Service latency incident is behind you, and Jordan's fix has been reviewed and is ready to ship on Monday. But something else is happening. Customers are complaining that their orders are failing, but your latency SLO looks fine. What is going on?*

### The Problem

The Inventory Service v1.1-bad introduces a random 30% failure rate. Unlike the latency issue, this does not affect response time. Instead, requests randomly return errors. The SLO for availability will catch this, but participants need to investigate why.

### Bad Code (Inventory Service)

```python
import random

@app.post("/api/inventory/check")
async def check_stock(request: StockCheckRequest):
    logger.info(f"Checking stock for {len(request.items)} items")

    # THE BUG: Random failures introduced in v1.1
    if random.random() < 0.30:
        logger.error("Database connection timeout (simulated)")
        raise HTTPException(
            status_code=503,
            detail="Inventory database temporarily unavailable"
        )

    # Normal stock check logic...
```

### Detection Methods

1. **Availability SLO:** Burns error budget due to increased error rate
2. **Error Rate Metric:** Visible spike in APM error rate chart
3. **Log Pattern:** "Database connection timeout" appears frequently
4. **ML Anomaly:** Error rate anomaly detected

### Investigation Steps

1. **Notice the SLO degradation:**
   - Navigate to SLOs
   - See Availability SLO burning (Latency SLO is fine)
   - Note the difference in affected SLOs

2. **Identify the failing service:**
   - Open APM Service Map
   - Inventory Service shows red (errors)
   - Order Service shows amber (dependent failures)

3. **Analyze error patterns:**
   - Open Inventory Service in APM
   - Click "Errors" tab
   - See "503 Service Unavailable" errors

4. **Correlate with logs:**
   - Open Logs
   - Filter: `service.name: inventory-service AND log.level: error`
   - See pattern: "Database connection timeout (simulated)"

5. **Identify the version:**
   - Check service.version in error transactions
   - Note: All errors are v1.1-bad
   - Compare with deployment timeline

### Key Learnings

- Not all problems manifest as latency
- Availability SLOs catch error rate issues
- Log pattern analysis reveals root cause
- ML can detect behavioral changes beyond just latency

### Deploy Command

```bash
./deploy.sh inventory-service v1.1-bad
```

### Rollback Command

```bash
./deploy.sh inventory-service v1.0
```

---

## Bonus Challenge B: The Slow Burn

**Difficulty:** Advanced
**Duration:** 30-45 minutes
**Focus:** Memory leak detection, infrastructure metrics, gradual degradation

### Scenario

> *It is Sunday evening. The weekend has been quiet since the incidents. You are doing a final check before the Monday rush when you notice something odd. Payment Service response times are creeping up. Not dramatically, like the Order Service incident, but slowly, steadily. By the time an alert fires, it might be too late. Can you catch a slow burn before it becomes a fire?*

### The Problem

The Payment Service v1.1-bad introduces a memory leak. Each request allocates memory that is never freed. Over time, the service becomes slower due to garbage collection pressure, and eventually crashes. This is a "slow burn" problem that SLO burn rate alerts might miss until it is critical.

### Bad Code (Payment Service)

```python
# Global memory leak list
leaked_data = []

@app.post("/api/payments")
async def process_payment(request: PaymentRequest):
    logger.info(f"Processing payment for order {request.order_id}")

    # THE BUG: Memory leak - data is never cleared
    transaction_record = {
        "order_id": request.order_id,
        "amount": request.amount,
        "timestamp": datetime.utcnow().isoformat(),
        "large_payload": "x" * 10000  # 10KB per request
    }
    leaked_data.append(transaction_record)

    logger.debug(f"Transaction cache size: {len(leaked_data)} entries")

    # Normal payment processing...
```

### Detection Methods

1. **Infrastructure Metrics:** Memory usage increasing over time
2. **Latency Trend:** Gradual latency increase (not sudden spike)
3. **Log Pattern:** "Transaction cache size" growing in logs
4. **ML Anomaly:** Detects unusual memory consumption pattern

### Investigation Steps

1. **Notice the trend (not spike):**
   - Open APM > Payment Service
   - Look at latency chart over 1 hour
   - Notice gradual upward trend (not sudden spike)

2. **Check infrastructure metrics:**
   - Navigate to Infrastructure > Hosts or Containers
   - Select payment-service container
   - View memory usage over time
   - Notice steady climb (sawtooth pattern from GC)

3. **Correlate metrics with latency:**
   - Overlay memory usage and latency charts
   - Notice correlation: higher memory = higher latency
   - GC pauses causing latency spikes

4. **Analyze logs for clues:**
   - Open Logs
   - Filter: `service.name: payment-service`
   - Search: "cache size"
   - See entry count growing

5. **Use ML Anomaly Detection:**
   - Open ML > Anomaly Explorer
   - See memory anomaly scored
   - Drill down to affected time range

6. **Identify root cause:**
   - Check deployment timeline
   - v1.1-bad deployed correlates with start of memory growth
   - Review code changes (via Agent Builder)

### Key Learnings

- Not all problems are immediate
- Infrastructure metrics complement APM data
- Trend analysis catches gradual degradation
- Proactive monitoring prevents outages

### Deploy Command

```bash
./deploy.sh payment-service v1.1-bad
```

### Recovery

This scenario does not have automated rollback configured. Participants must:

1. Recognize the problem from metrics
2. Manually execute rollback:
   ```bash
   ./deploy.sh payment-service v1.0
   ```
3. Observe memory stabilize and latency recover

### Challenge Extension

For advanced participants, suggest:
- Set up a custom alert on memory usage trend
- Create a runtime log query rule for "cache size > 1000"
- Discuss how to add circuit breakers

---

## Bonus Challenge C: The Cascading Failure (Self-Guided)

**Difficulty:** Advanced
**Duration:** 45-60 minutes
**Focus:** Distributed tracing, dependency analysis, circuit breakers

### Scenario

> *What happens when everything goes wrong at once? In this challenge, you will deploy bad versions of multiple services and watch how failures cascade through the system. Your job is to identify the root cause in a storm of alerts.*

### The Setup

Deploy bad versions of all three services:

```bash
./deploy.sh order-service v1.1-bad      # 2s latency
./deploy.sh inventory-service v1.1-bad  # 30% error rate
./deploy.sh payment-service v1.1-bad    # Memory leak
```

### The Challenge

1. Multiple alerts fire simultaneously
2. Service map shows multiple red nodes
3. Determine which problem to fix first
4. Prioritize based on business impact

### Investigation Questions

1. Which service is the root cause vs. victim?
2. How do you prioritize when everything is failing?
3. What is the total business impact?
4. How would you communicate this to stakeholders?

### Solution Approach

1. **Triage by impact:**
   - Order Service latency affects all orders
   - Inventory errors fail 30% of orders
   - Payment leak is slow-building

2. **Fix order of priority:**
   - Order Service first (immediate, high impact)
   - Inventory Service second (significant error rate)
   - Payment Service third (slow burn, can wait)

3. **Execute rollbacks:**
   ```bash
   ./deploy.sh order-service v1.0
   ./deploy.sh inventory-service v1.0
   ./deploy.sh payment-service v1.0
   ```

4. **Verify recovery:**
   - Watch SLOs recover
   - Confirm alerts resolve
   - Check all services healthy

---

## Agent Builder Practice Queries

Use these queries with Agent Builder to practice conversational investigation:

### Timeline Queries
- "What deployments happened in the last 2 hours?"
- "When did the first error occur after the deployment?"
- "Create a timeline of the incident from deployment to recovery"

### Impact Queries
- "How many orders failed during the incident?"
- "What was the total revenue impact?"
- "Which customers were affected?"

### Comparison Queries
- "Compare latency between v1.0 and v1.1"
- "What is different about failed requests vs successful ones?"
- "Show me the error rate before and after the deployment"

### Root Cause Queries
- "What changed in the code between v1.0 and v1.1?"
- "Who made the last deployment?"
- "What was the commit message for the failing version?"

### Health Queries
- "What is the current health of all services?"
- "Are there any active alerts?"
- "What is our current SLO status?"

---

## Creating Custom Scenarios

### Framework for New Scenarios

1. **Choose a failure mode:**
   - Latency (sleep, slow query, network delay)
   - Errors (exceptions, timeouts, 5xx responses)
   - Resource exhaustion (memory, CPU, connections)
   - Data issues (corruption, inconsistency)

2. **Select a detection method:**
   - SLO burn rate
   - Threshold alert
   - ML anomaly
   - Log pattern
   - Infrastructure metric

3. **Design the investigation path:**
   - What will participants see first?
   - What will they drill down into?
   - What is the "aha moment"?

4. **Create the bad code:**
   - Make it believable (something a real developer might write)
   - Include attribution (author, commit, PR)
   - Add relevant logging

5. **Write the narrative:**
   - Who deploys it?
   - When is it discovered?
   - What is the business impact?

### Example: Custom Scenario Template

```markdown
## Scenario Name: [Title]

### The Problem
[One sentence describing the technical issue]

### Bad Code
[Code snippet showing the bug]

### Detection
[Which Elastic feature catches this first]

### Investigation Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Key Learning
[What participants learn from this scenario]
```

---

## Self-Assessment Questions

After completing the bonus challenges, participants should be able to answer:

1. **Detection:** How do different types of failures manifest in observability data?

2. **Prioritization:** When multiple alerts fire, how do you decide what to fix first?

3. **Correlation:** How do you connect traces, logs, and metrics to build a complete picture?

4. **Attribution:** How can telemetry help identify who made what change and when?

5. **Automation:** What types of problems are good candidates for automated remediation?

6. **Prevention:** How would you prevent these types of issues in the future?

---

## Additional Resources

- [Elastic Observability Documentation](https://www.elastic.co/docs/solutions/observability)
- [SLO Best Practices](https://www.elastic.co/docs/solutions/observability/incident-management/service-level-objectives-slos)
- [APM Correlations Guide](https://www.elastic.co/docs/solutions/observability/apm)
- [ML Anomaly Detection](https://www.elastic.co/docs/explore-analyze/machine-learning)
