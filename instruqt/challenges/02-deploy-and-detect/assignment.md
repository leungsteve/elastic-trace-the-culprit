---
slug: 02-deploy-and-detect
id: 02-deploy-and-detect
type: challenge
title: "Deploy and Detect"
teaser: "Deploy a new version and watch the alerts fire"
---

# Deploy and Detect

> At 2:47 PM, a message appears in the #deployments Slack channel:
>
> **jordan.rivera:** Just shipped v1.1 with some performance optimizations. QA signed off. Happy Friday everyone! 🚀
>
> You note the deployment and continue your work. Five minutes later, your phone buzzes. An alert has fired. Your weekend plans are about to change.

## Your Mission

In this challenge, you will:

1. Deploy the new version (v1.1-bad) of the Order Service
2. Observe the immediate impact on latency and SLOs
3. Watch alerts fire automatically
4. Calculate business impact in real-time
5. Understand how Elastic detects problems proactively

## Step 1: Review the Deployment Command

Before deploying, let's understand what we are about to do.

The `deploy.sh` script simulates a CI/CD deployment:
1. Updates the service version in the environment configuration
2. Restarts the container with the new image
3. Sends a deployment annotation to Elastic APM
4. Performs a health check

Review the command:

```bash
./scripts/deploy.sh order-service v1.1-bad
```

This will deploy version `v1.1-bad` of the Order Service.

## Step 2: Prepare to Observe

Before deploying, open the following pages in Kibana (in separate tabs or windows):

### Tab 1: SLO Dashboard
**Observability > SLOs**

Keep this page visible. You will watch the SLO status change in real-time.

### Tab 2: Order Service APM
**Observability > APM > Services > order-service**

This will show latency charts and throughput metrics.

### Tab 3: Alerts
**Observability > Alerts**

You will see alerts appear here when thresholds are breached.

## Step 3: Deploy the Bad Code

Now, execute the deployment:

```bash
cd /root/from-commit-to-culprit
./scripts/deploy.sh order-service v1.1-bad
```

You should see output like:

```
═══════════════════════════════════════════════════════════════
  DEPLOYMENT INITIATED
═══════════════════════════════════════════════════════════════
  Service:     order-service
  Version:     v1.1-bad
  Timestamp:   2024-01-15T14:47:00.000Z
  Commit:      a1b2c3d4
  Author:      jordan.rivera
  PR:          #1247
═══════════════════════════════════════════════════════════════
```

The deployment annotation will appear as a vertical line in APM charts.

## Step 4: Watch the Impact Unfold

Immediately after deployment, switch to your Kibana tabs and observe:

### In the Order Service APM page:

Watch the **Latency** chart:
- Before deployment: ~100-300ms average
- After deployment: Should spike to ~2000ms immediately
- Look for the deployment annotation (vertical line) on the chart

> 📸 **Screenshot: Latency Spike After Deployment**
>
> ![Latency Spike](screenshots/02-latency-spike.png)
>
> *Shows the APM latency chart with a dramatic spike from ~200ms to ~2000ms. A vertical deployment annotation line marks exactly when v1.1-bad was deployed. The correlation between deployment and spike should be visually obvious.*

### In the SLO Dashboard:

Watch the **Order Service - Latency P95 < 500ms** SLO:
- **SLI percentage** will start dropping (requests no longer meeting the 500ms target)
- **Burn rate** will increase dramatically (6x or higher)
- The status indicator will turn yellow or red

> 📸 **Screenshot: SLO Degradation**
>
> ![SLO Degradation](screenshots/02-slo-degradation.png)
>
> *Shows the SLO dashboard with the Latency SLO now showing yellow/red status. The SLI percentage has dropped, burn rate shows elevated consumption (6x+), and error budget is being consumed rapidly. Compare this to the healthy state from Challenge 1.*

This should happen within **2-3 minutes** of the deployment.

### Expected Timeline:

```
T+0:00  - Deployment executed
T+0:30  - First slow requests appear
T+2:00  - SLO burn rate exceeds threshold
T+3:00  - Alert fires (you'll see it in Observability > Alerts)
```

## Step 5: Observe the Business Impact

Return to **Observability > APM > Services > order-service** and observe the impact:

- **Latency chart:** Requests are now taking ~2000ms instead of ~100-300ms
- **Failed transaction rate:** May show increased failures due to timeouts
- **Throughput:** Requests per minute may drop as the system struggles

You can estimate revenue impact using the formula:
```
Revenue Impact = Failed Orders × $47.50 (average order value)
```

In Challenge 4, you will use Agent Builder to calculate the exact business impact.

## Step 6: Watch the Alert Fire

Navigate to **Observability > Alerts**.

Within 3-5 minutes of deployment, you should see an alert:

**Alert:** Order Service SLO Burn Rate
**Severity:** High
**Status:** Active
**Message:** SLO burn rate exceeds 6x sustainable rate

Click on the alert to see details:
- When it fired
- Current burn rate
- Link to the affected SLO
- Link to investigate in APM

> 📸 **Screenshot: Alert Fired**
>
> ![Alert Fired](screenshots/02-alert-fired.png)
>
> *Shows the Alerts page with the "SLO Burn Rate" alert in Active/Firing state. The alert details panel shows severity, when it fired, and the current burn rate value exceeding the threshold.*

## Step 7: Examine the Deployment Annotation

Return to **Observability > APM > Services > order-service**.

Look at the latency chart. You should see:
- A vertical line marking the deployment
- Latency dramatically increasing immediately after that line

Hover over the annotation to see deployment metadata:
- Version: v1.1-bad
- Author: jordan.rivera
- Commit: a1b2c3d4
- PR: #1247

This visual correlation makes it obvious that the deployment caused the issue.

## Checkpoint

Before moving to the next challenge, verify:

- [ ] order-service v1.1-bad is deployed and running
- [ ] Latency has increased to ~2000ms
- [ ] SLO burn rate is elevated (6x or higher)
- [ ] Alert has fired (visible in Observability > Alerts)
- [ ] Deployment annotation is visible in APM

## What You Learned

In this challenge, you:
- Executed a deployment simulation
- Observed immediate impact on service latency
- Watched SLO burn rate exceed sustainable thresholds
- Saw alerts fire automatically based on SLO conditions
- Calculated business impact of the degradation
- Correlated the incident with the deployment using annotations

The alert has fired, but the system is still degraded. Time to investigate and remediate.

---

**Pro Tip:** Notice how quickly the alert fired. Traditional threshold alerts might miss gradual degradations, but SLO burn rate alerts detect problems based on the rate of error budget consumption. This enables faster detection and response.
