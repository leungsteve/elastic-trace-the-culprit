---
slug: 01-setup-and-baseline
id: 01-setup-and-baseline
type: challenge
title: "Setup and Baseline"
teaser: "Verify your environment and establish what 'healthy' looks like"
---

# Setup and Baseline

> It is Friday afternoon at NovaMart headquarters. The week has been uneventful. Order volumes are steady. No pages overnight. You are Alex Chen, the on-call SRE for the weekend shift.
>
> Before heading into the weekend, you want to make sure everything looks healthy. Sam Patel, your manager, always says: "You cannot detect anomalies if you do not know what normal looks like."

## Your Mission

In this challenge, you will:

1. Verify all services are running and sending telemetry to Elastic
2. Explore the service architecture in APM
3. Review the baseline SLO status
4. Generate some healthy traffic
5. Understand what "normal" looks like

## Step 1: Verify Service Health

Let's make sure all services are running properly.

```bash
cd /root/from-commit-to-culprit
./scripts/health-check.sh
```

You should see all three services reporting healthy status:
- **order-service** (Port 8088)
- **inventory-service** (Port 8081)
- **payment-service** (Port 8082)

## Step 2: Explore Services in APM

Switch to the **Kibana** tab and navigate to:

**Observability > APM > Services**

You should see three services listed:
- `order-service`
- `inventory-service`
- `payment-service`

> 📸 **Screenshot: APM Services List**
>
> ![APM Services](screenshots/01-apm-services-list.png)
>
> *Shows the three services (order-service, inventory-service, payment-service) in the APM Services view with healthy status indicators and baseline metrics.*

Click on **order-service** to view its details. Note the baseline metrics:
- **Latency:** Should be around 100-300ms
- **Throughput:** Requests per minute
- **Failed transaction rate:** Should be near 0%

### Explore the Service Map

Navigate to **Observability > APM > Service Map**

This visual representation shows how services connect:
- **order-service** calls both **inventory-service** and **payment-service**
- All three services send data to the EDOT Collector

> 📸 **Screenshot: Service Map**
>
> ![Service Map](screenshots/01-service-map.png)
>
> *Shows order-service in the center with arrows connecting to inventory-service and payment-service, visualizing the microservice dependencies.*

## Step 3: Review SLOs

Navigate to **Observability > SLOs** in Kibana.

You should see two Service Level Objectives configured:

### Order Service - Latency P95 < 500ms
- **Target:** 95% of requests complete in less than 500ms
- **Window:** 7-day rolling window
- **Current Status:** Should be healthy (green)

### Order Service - Availability 99%
- **Target:** 99% of requests succeed
- **Window:** 30-day rolling window
- **Current Status:** Should be healthy (green)

> 📸 **Screenshot: SLO Dashboard - Healthy State**
>
> ![SLO Dashboard](screenshots/01-slo-dashboard-healthy.png)
>
> *Shows both SLOs with green status indicators, high SLI percentages (99%+), and minimal error budget consumption. This is what "healthy" looks like.*

Click on the **Order Service - Latency P95 < 500ms** SLO to view details. Note:
- **SLI (Service Level Indicator):** The current percentage meeting the target
- **Error Budget:** The remaining buffer before violating the SLO
- **Burn Rate:** How quickly the error budget is being consumed

Take a moment to understand these concepts. They will be critical during the incident.

## Step 4: Generate Baseline Traffic

Let's generate some realistic traffic to establish a baseline.

```bash
./scripts/load-generator.sh &
```

This script will send random order requests to the Order Service at a rate of 2-5 requests per second.

Wait about 2 minutes for traffic to flow, then return to Kibana.

## Step 5: Explore a Healthy Trace

Navigate to **Observability > APM > Traces** in Kibana.

Click on any recent trace to see the distributed trace waterfall. A healthy order request flows like this:

```
order-service
├── POST /api/orders (100-300ms)
    ├── inventory-service
    │   └── POST /api/inventory/check (20-50ms)
    ├── inventory-service
    │   └── POST /api/inventory/reserve (20-50ms)
    └── payment-service
        └── POST /api/payments (30-80ms)
```

> 📸 **Screenshot: Healthy Trace Waterfall**
>
> ![Healthy Trace](screenshots/01-healthy-trace-waterfall.png)
>
> *Shows a normal trace with total duration ~100-300ms. The waterfall displays order-service as the parent span with child spans for inventory and payment calls. Note the short, proportional span durations.*

Notice the span attributes on the right panel. Each span includes:
- Service name and version
- Duration
- Status (success/failure)

**Important:** Take note of the current `service.version` for order-service. It should be `v1.0`.

## Step 6: Explore Log Correlation

While viewing a trace, copy the **trace.id** from the metadata section.

Navigate to **Observability > Logs > Stream** and add a filter:

```
trace.id: <paste-the-trace-id>
```

You should see all log messages from all services involved in that specific request. This is **log correlation** in action. Notice how each log message includes:
- Timestamp
- Service name
- Log level
- The trace ID
- File and line number

This will be crucial when investigating issues.

## Checkpoint

Before moving to the next challenge, verify:

- [ ] All three services are visible in APM
- [ ] Both SLOs show healthy (green) status
- [ ] Load generator is running in the background
- [ ] You understand what a healthy trace looks like
- [ ] You can correlate traces with logs using trace.id

## What You Learned

In this challenge, you:
- Verified environment connectivity to Elastic Cloud Serverless
- Explored the service architecture and dependencies
- Understood SLO concepts (SLI, error budget, burn rate)
- Established a mental model of "healthy" baseline behavior
- Learned to navigate between APM, traces, and logs

You are now ready to detect anomalies.

---

**Pro Tip:** Keep the **Observability > SLOs** page open in a browser tab. You will want to watch it during the next challenge.
