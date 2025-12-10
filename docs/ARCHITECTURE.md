# Architecture Document

## From Commit to Culprit: An Elastic Observability Workshop

**Version:** 1.0  
**Last Updated:** December 2024  
**Author:** Solutions Architecture Team

---

## System Overview

The workshop environment consists of three microservices running in Docker containers, an EDOT Collector for telemetry aggregation, a local container registry, and a rollback webhook service. All telemetry flows to Elastic Cloud Serverless.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           INSTRUQT VM / LOCAL HOST                              │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         DOCKER NETWORK                                   │   │
│  │                                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │   │
│  │  │    Order     │  │  Inventory   │  │   Payment    │                   │   │
│  │  │   Service    │  │   Service    │  │   Service    │                   │   │
│  │  │   (Java)     │  │  (Python)    │  │  (Python)    │                   │   │
│  │  │   :8088      │  │   :8081      │  │   :8082      │                   │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                   │   │
│  │         │                 │                 │                            │   │
│  │         └─────────────────┼─────────────────┘                            │   │
│  │                           │                                              │   │
│  │                    ┌──────▼──────┐                                       │   │
│  │                    │    EDOT     │                                       │   │
│  │                    │  Collector  │                                       │   │
│  │                    │  :4317/4318 │                                       │   │
│  │                    └──────┬──────┘                                       │   │
│  │                           │                                              │   │
│  │  ┌──────────────┐         │         ┌──────────────┐                    │   │
│  │  │   Rollback   │         │         │    Local     │                    │   │
│  │  │   Webhook    │         │         │   Registry   │                    │   │
│  │  │   :9000      │         │         │   :5000      │                    │   │
│  │  └──────────────┘         │         └──────────────┘                    │   │
│  │                           │                                              │   │
│  └───────────────────────────┼──────────────────────────────────────────────┘   │
│                              │                                                  │
└──────────────────────────────┼──────────────────────────────────────────────────┘
                               │
                               │ HTTPS (OTLP)
                               │
                               ▼
              ┌────────────────────────────────────┐
              │     ELASTIC CLOUD SERVERLESS       │
              │                                    │
              │  ┌────────────────────────────┐   │
              │  │          APM               │   │
              │  │  • Traces                  │   │
              │  │  • Service Map             │   │
              │  │  • Correlations            │   │
              │  │  • Anomaly Detection       │   │
              │  └────────────────────────────┘   │
              │                                    │
              │  ┌────────────────────────────┐   │
              │  │         SLOs               │   │
              │  │  • Latency SLO             │   │
              │  │  • Availability SLO        │   │
              │  │  • Burn Rate Alerts        │   │
              │  └────────────────────────────┘   │
              │                                    │
              │  ┌────────────────────────────┐   │
              │  │       Workflows            │   │
              │  │  • Webhook Connector       │   │
              │  │  • Auto-Rollback Action    │   │
              │  └────────────────────────────┘   │
              │                                    │
              │  ┌────────────────────────────┐   │
              │  │     Agent Builder          │   │
              │  │  • Investigation Agent     │   │
              │  │  • 7 Custom Tools          │   │
              │  └────────────────────────────┘   │
              │                                    │
              └────────────────────────────────────┘
```

---

## Component Architecture

### Application Services

#### Order Service

**Technology:** Java 21, Spring Boot 3.x

**Responsibilities:**
- Accept order requests from customers
- Validate order data
- Orchestrate calls to Inventory and Payment services
- Return order confirmation or error

**Communication Pattern:**
- Synchronous HTTP to Inventory Service
- Synchronous HTTP to Payment Service
- Traces propagated via W3C headers

```
┌─────────────────────────────────────────────────────────────┐
│                     ORDER SERVICE                           │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Controller │───►│   Service   │───►│   Client    │     │
│  │             │    │   Layer     │    │   Layer     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                                    │              │
│         ▼                                    ▼              │
│  ┌─────────────┐                      ┌───────────────┐    │
│  │   EDOT      │                      │ RestTemplate  │    │
│  │   Agent     │                      │ (instrumented)│    │
│  └─────────────┘                      └───────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Inventory Service

**Technology:** Python 3.11, FastAPI

**Responsibilities:**
- Maintain in-memory product inventory
- Check stock availability for orders
- Return stock status

**Data Model:**
```python
inventory = {
    "LAPTOP-001": 50,
    "PHONE-002": 100,
    "TABLET-003": 75,
    "HEADPHONES-004": 200,
}
```

#### Payment Service

**Technology:** Python 3.11, FastAPI

**Responsibilities:**
- Process payment transactions
- Simulate payment gateway behavior
- Return payment confirmation

**Behavior:**
- 99% success rate (1% random failures for realism)
- Deterministic based on seed for reproducibility

---

### Infrastructure Components

#### OTel Collector

**Image:** `otel/opentelemetry-collector-contrib:0.91.0`

> **Note:** This version should be updated periodically to stay current with releases.

**Configuration:**
- Receives OTLP on gRPC (4317) and HTTP (4318)
- Batches telemetry for efficiency
- Adds resource attributes
- Exports to Elastic APM endpoint

**Pipeline:**
```
Traces  ─┐
         ├──► Batch Processor ──► Resource Processor ──► OTLP Exporter
Metrics ─┤                                                    │
         │                                                    ▼
Logs   ──┘                                            Elastic Cloud
```

#### Local Container Registry

**Image:** `registry:2.8.3`

**Purpose:**
- Store pre-built Docker images
- Avoid internet dependencies during workshop
- Enable fast image pulls

**Images Stored:**
```
localhost:5000/order-service:v1.0
localhost:5000/order-service:v1.1-bad
localhost:5000/inventory-service:v1.0
localhost:5000/inventory-service:v1.1-bad
localhost:5000/payment-service:v1.0
localhost:5000/payment-service:v1.1-bad
localhost:5000/rollback-webhook:latest
```

#### Rollback Webhook Service

**Technology:** Python 3.11, FastAPI

**Purpose:**
- Receive POST requests from Elastic Workflows
- Execute docker-compose commands to swap versions
- Report rollback status

**Permissions:**
- Mounted Docker socket for container management
- Mounted .env file for version updates
- Mounted docker-compose.yml for orchestration

### Webhook Connectivity (Instruqt)

In the Instruqt environment, the rollback webhook must be accessible from Elastic Cloud. Instruqt's built-in service exposure creates a public URL for the webhook.

**Instruqt track.yml configuration:**

```yaml
tabs:
- title: Terminal
  type: terminal
  hostname: workshop-vm
- title: Rollback Webhook
  type: service
  hostname: workshop-vm
  port: 9000
  path: /
```

This creates a public URL like `https://<track-id>-9000.instruqt.io` that Elastic Cloud can reach.

**Environment variable:** The `setup-elastic.sh` script accepts `WEBHOOK_PUBLIC_URL` as an environment variable and uses it when creating the webhook connector in Elastic:

```bash
# In Instruqt setup.sh
export WEBHOOK_PUBLIC_URL="https://${INSTRUQT_PARTICIPANT_ID}-9000.instruqt.io"
./scripts/setup-elastic.sh
```

**Local development:** For local development with Elastic Cloud Serverless, use a tunnel service (e.g., ngrok) to expose the webhook:

```bash
# Start ngrok tunnel
ngrok http 9000

# Set the public URL in .env.local
WEBHOOK_PUBLIC_URL=https://abc123.ngrok.io
```

This allows the Elastic Workflow to reach the local rollback webhook service.

> **Note:** If using start-local (not recommended), Workflows are not available and automated rollback will not function.

---

## Data Flow

### Normal Request Flow

```
┌──────────┐    POST /api/orders    ┌──────────────┐
│  Client  │───────────────────────►│    Order     │
│  (curl)  │                        │   Service    │
└──────────┘                        └──────┬───────┘
                                           │
                                           │ 1. Check stock
                                           ▼
                                    ┌──────────────┐
                                    │  Inventory   │
                                    │   Service    │
                                    └──────┬───────┘
                                           │
                                           │ 2. Stock OK
                                           ▼
                                    ┌──────────────┐
                                    │   Payment    │
                                    │   Service    │
                                    └──────┬───────┘
                                           │
                                           │ 3. Payment OK
                                           ▼
                                    ┌──────────────┐
                                    │    Order     │
                                    │   Service    │
                                    └──────┬───────┘
                                           │
                                           │ 4. Return order
                                           ▼
                                    ┌──────────────┐
                                    │   Client     │
                                    └──────────────┘
```

### Telemetry Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            SERVICE CONTAINERS                                   │
│                                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                              TRACE                                      │    │
│  │                                                                         │    │
│  │  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐             │    │
│  │  │ Order Span  │─────►│ Inventory   │─────►│ Payment     │             │    │
│  │  │ (parent)    │      │ Span (child)│      │ Span (child)│             │    │
│  │  │             │      │             │      │             │             │    │
│  │  │ trace_id:   │      │ trace_id:   │      │ trace_id:   │             │    │
│  │  │ abc123      │      │ abc123      │      │ abc123      │             │    │
│  │  └─────────────┘      └─────────────┘      └─────────────┘             │    │
│  │                                                                         │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                              LOGS                                       │    │
│  │                                                                         │    │
│  │  [abc123] Order Service: Creating order for customer cust-001           │    │
│  │  [abc123] Inventory Service: Checking stock for LAPTOP-001              │    │
│  │  [abc123] Payment Service: Processing payment $999.99                   │    │
│  │  [abc123] Order Service: Order created successfully                     │    │
│  │                                                                         │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                             METRICS                                     │    │
│  │                                                                         │    │
│  │  http_server_duration_bucket{service="order-service", le="500"} 45     │    │
│  │  http_server_duration_bucket{service="order-service", le="1000"} 47    │    │
│  │  http_server_duration_count{service="order-service"} 50                │    │
│  │                                                                         │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ OTLP (gRPC/HTTP)
                                        ▼
                              ┌──────────────────┐
                              │  OTel Collector  │
                              └────────┬─────────┘
                                       │
                                       │ OTLP (HTTPS)
                                       ▼
                              ┌──────────────────┐
                              │  Elastic Cloud   │
                              └──────────────────┘
```

### Incident Detection and Remediation Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DETECTION AND REMEDIATION                               │
│                                                                                 │
│  TIME ─────────────────────────────────────────────────────────────────────►   │
│                                                                                 │
│  14:47:00                                                                       │
│  ┌─────────────────┐                                                           │
│  │ Deploy v1.1-bad │                                                           │
│  │ (deploy.sh)     │                                                           │
│  └────────┬────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  14:47:23 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│  ┌─────────────────┐                                                           │
│  │ First slow      │   Latency: 2,347ms (was ~200ms)                           │
│  │ transaction     │                                                           │
│  └────────┬────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  14:48:00 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│  ┌─────────────────┐   ┌─────────────────┐                                     │
│  │ SLO degrading   │   │ ML anomaly      │                                     │
│  │ Burn rate > 1x  │   │ detected        │                                     │
│  └────────┬────────┘   └─────────────────┘                                     │
│           │                                                                     │
│           ▼                                                                     │
│  14:49:00 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│  ┌─────────────────┐                                                           │
│  │ Burn rate > 6x  │   Threshold exceeded                                      │
│  │ Alert fires     │                                                           │
│  └────────┬────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  14:49:15 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│  ┌─────────────────┐                                                           │
│  │ Workflow        │                                                           │
│  │ triggers        │────────────────────────┐                                  │
│  └─────────────────┘                        │                                  │
│                                             ▼                                  │
│  14:49:18 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┌─────────────────┐─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│                                    │ Webhook POST    │                         │
│                                    │ to :9000        │                         │
│                                    └────────┬────────┘                         │
│                                             │                                  │
│                                             ▼                                  │
│  14:49:20 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┌─────────────────┐─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│                                    │ docker-compose  │                         │
│                                    │ up order:v1.0   │                         │
│                                    └────────┬────────┘                         │
│                                             │                                  │
│                                             ▼                                  │
│  14:51:00 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│  ┌─────────────────┐                                                           │
│  │ Service         │   Latency returns to ~200ms                               │
│  │ recovered       │                                                           │
│  └────────┬────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  14:53:00 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│  ┌─────────────────┐                                                           │
│  │ Alert resolved  │   SLO burn rate < 1x                                      │
│  └─────────────────┘                                                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Elastic Configuration

### Service Level Objectives (SLOs)

**Order Latency SLO:**
```json
{
  "name": "Order Service Latency",
  "description": "95% of order requests complete in under 500ms",
  "indicator": {
    "type": "sli.apm.transactionDuration",
    "params": {
      "service": "order-service",
      "environment": "workshop",
      "transactionType": "request",
      "transactionName": "POST /api/orders",
      "threshold": 500,
      "index": "metrics-apm*"
    }
  },
  "timeWindow": {
    "duration": "1h",
    "type": "rolling"
  },
  "budgetingMethod": "occurrences",
  "objective": {
    "target": 0.95
  }
}
```

**Order Availability SLO:**
```json
{
  "name": "Order Service Availability",
  "description": "99% of order requests succeed",
  "indicator": {
    "type": "sli.apm.transactionErrorRate",
    "params": {
      "service": "order-service",
      "environment": "workshop",
      "transactionType": "request",
      "transactionName": "POST /api/orders",
      "index": "metrics-apm*"
    }
  },
  "timeWindow": {
    "duration": "1h",
    "type": "rolling"
  },
  "budgetingMethod": "occurrences",
  "objective": {
    "target": 0.99
  }
}
```

### Alert Rules

**SLO Burn Rate Alert:**
```json
{
  "name": "Order Service SLO Burn Rate",
  "rule_type_id": "slo.rules.burnRate",
  "params": {
    "sloId": "order-latency-slo",
    "windows": [
      {
        "burnRateThreshold": 6,
        "longWindow": { "value": 1, "unit": "h" },
        "shortWindow": { "value": 5, "unit": "m" }
      }
    ]
  },
  "actions": [
    {
      "id": "rollback-webhook-connector",
      "group": "slo.burnRate.alert",
      "params": {
        "body": {
          "service": "order-service",
          "target_version": "v1.0",
          "alert_id": "{{alertId}}",
          "reason": "SLO burn rate exceeded threshold"
        }
      }
    }
  ]
}
```

**Threshold Alert (Backup):**
```json
{
  "name": "Order Service High Latency",
  "rule_type_id": "apm.transaction_duration",
  "params": {
    "serviceName": "order-service",
    "transactionType": "request",
    "windowSize": 5,
    "windowUnit": "m",
    "threshold": 2000,
    "aggregationType": "avg"
  }
}
```

### Workflow Configuration

**Webhook Connector:**
```json
{
  "name": "Rollback Webhook",
  "connector_type_id": ".webhook",
  "config": {
    "url": "http://rollback-webhook:9000/rollback",
    "method": "post",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

### Agent Builder Configuration

**Agent:**
```json
{
  "name": "Incident Investigator",
  "description": "AI assistant for investigating production incidents",
  "system_prompt": "You are an expert SRE assistant helping investigate production incidents at NovaMart. Always calculate business impact using $47.50 average order value. Be concise and actionable.",
  "tools": [
    "apm-latency-comparison",
    "deployment-timeline",
    "error-pattern-analysis",
    "incident-timeline",
    "service-health-snapshot",
    "slo-status-budget",
    "business-impact-calculator"
  ]
}
```

**Sample Tool (Business Impact Calculator):**
```json
{
  "name": "business-impact-calculator",
  "description": "Calculate revenue impact of service degradation",
  "parameters": {
    "type": "object",
    "properties": {
      "start_time": {
        "type": "string",
        "description": "Start of incident window (ISO format)"
      },
      "end_time": {
        "type": "string",
        "description": "End of incident window (ISO format)"
      },
      "service": {
        "type": "string",
        "description": "Service name",
        "default": "order-service"
      }
    },
    "required": ["start_time"]
  },
  "query": {
    "index": "traces-apm*",
    "body": {
      "query": {
        "bool": {
          "must": [
            { "term": { "service.name": "{{service}}" } },
            { "range": { "@timestamp": { "gte": "{{start_time}}", "lte": "{{end_time}}" } } }
          ]
        }
      },
      "aggs": {
        "total_transactions": { "value_count": { "field": "transaction.id" } },
        "failed_transactions": {
          "filter": { "term": { "transaction.result": "error" } }
        }
      }
    }
  },
  "response_template": "During the incident window, there were {{total_transactions}} transactions with {{failed_transactions}} failures. At $47.50 average order value, this represents approximately ${{failed_transactions * 47.50}} in lost revenue."
}
```

---

## Deployment Architecture

### Image Build Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BUILD PROCESS                                         │
│                                                                                 │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                     │
│  │  Source     │      │   Docker    │      │   Local     │                     │
│  │   Code      │─────►│   Build     │─────►│  Registry   │                     │
│  │             │      │             │      │  :5000      │                     │
│  └─────────────┘      └─────────────┘      └─────────────┘                     │
│                                                                                 │
│  For each service:                                                              │
│                                                                                 │
│  services/order-service/                                                        │
│  ├── Dockerfile       ──► order-service:v1.0                                   │
│  └── Dockerfile.bad   ──► order-service:v1.1-bad                               │
│                                                                                 │
│  services/inventory-service/                                                    │
│  ├── Dockerfile       ──► inventory-service:v1.0                               │
│  └── Dockerfile.bad   ──► inventory-service:v1.1-bad                           │
│                                                                                 │
│  services/payment-service/                                                      │
│  ├── Dockerfile       ──► payment-service:v1.0                                 │
│  └── Dockerfile.bad   ──► payment-service:v1.1-bad                             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Deployment Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DEPLOYMENT FLOW                                       │
│                                                                                 │
│  ┌─────────────┐                                                               │
│  │ deploy.sh   │                                                               │
│  │ order v1.1  │                                                               │
│  └──────┬──────┘                                                               │
│         │                                                                       │
│         ▼                                                                       │
│  ┌─────────────┐                                                               │
│  │ Update .env │   ORDER_SERVICE_VERSION=v1.1-bad                              │
│  └──────┬──────┘                                                               │
│         │                                                                       │
│         ▼                                                                       │
│  ┌─────────────┐                                                               │
│  │ docker pull │   localhost:5000/order-service:v1.1-bad                       │
│  └──────┬──────┘                                                               │
│         │                                                                       │
│         ▼                                                                       │
│  ┌─────────────┐                                                               │
│  │ docker-     │   up -d --no-deps order-service                               │
│  │ compose     │                                                               │
│  └──────┬──────┘                                                               │
│         │                                                                       │
│         ▼                                                                       │
│  ┌─────────────┐                                                               │
│  │ POST to     │   Deployment annotation with metadata                         │
│  │ Elastic APM │   (commit, author, PR)                                        │
│  └──────┬──────┘                                                               │
│         │                                                                       │
│         ▼                                                                       │
│  ┌─────────────┐                                                               │
│  │ Health      │   Verify service responds                                     │
│  │ check       │                                                               │
│  └─────────────┘                                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Network Architecture

### Docker Network Configuration

```yaml
networks:
  workshop:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

services:
  order-service:
    networks:
      workshop:
        ipv4_address: 172.28.0.10
  
  inventory-service:
    networks:
      workshop:
        ipv4_address: 172.28.0.11
  
  payment-service:
    networks:
      workshop:
        ipv4_address: 172.28.0.12
  
  otel-collector:
    networks:
      workshop:
        ipv4_address: 172.28.0.20
  
  rollback-webhook:
    networks:
      workshop:
        ipv4_address: 172.28.0.30
  
  registry:
    networks:
      workshop:
        ipv4_address: 172.28.0.40
```

### Port Mapping

| Service | Container Port | Host Port | Purpose |
|---------|---------------|-----------|---------|
| Order Service | 8080 | 8088 | HTTP API |
| Inventory Service | 8081 | 8081 | HTTP API |
| Payment Service | 8082 | 8082 | HTTP API |
| OTel Collector | 4317 | 4317 | OTLP gRPC |
| OTel Collector | 4318 | 4318 | OTLP HTTP |
| Rollback Webhook | 9000 | 9000 | Webhook endpoint |
| Registry | 5000 | 5000 | Docker registry |

---

## Security Architecture

### Secrets Management

| Secret | Storage | Access |
|--------|---------|--------|
| ELASTIC_API_KEY | .env file | Services, scripts |
| ELASTIC_ENDPOINT | .env file | Services, scripts |

### Access Control

- **Docker socket:** Mounted read-write only to rollback-webhook
- **Environment files:** Mounted read-only to services, read-write to rollback-webhook
- **Registry:** No authentication (local only)

### Network Security

- All inter-service communication on internal Docker network
- Only OTLP traffic leaves the Docker network (to Elastic Cloud)
- Webhook accessible only from Elastic Cloud via Instruqt tunnel

---

## Failure Modes

### Service Failures

| Failure | Detection | Impact | Recovery |
|---------|-----------|--------|----------|
| Order Service down | Health check fails | Orders cannot be placed | Restart container |
| Inventory Service down | Order Service errors | Stock checks fail | Restart container |
| Payment Service down | Order Service errors | Payments fail | Restart container |
| Collector down | No telemetry in Elastic | Blind operations | Restart container |

### Workshop-Specific Failures

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Bad code does not deploy | No latency spike | Verify image in registry |
| Alert does not fire | No Workflow trigger | Check alert rule status |
| Rollback fails | Service stays slow | Manual rollback via deploy.sh |
| Agent Builder unavailable | 404 error | Skip Challenge 4 Agent section |

---

## Monitoring the Workshop

### Health Indicators

| Indicator | Healthy Value | Check Command |
|-----------|---------------|---------------|
| Services running | 3/3 | `docker-compose ps` |
| Traces flowing | > 0/min | Check APM UI |
| SLOs computed | 2 active | Check SLO UI |
| Alerts configured | 2 rules | Check Rules UI |

### Troubleshooting Commands

```bash
# Check service logs
docker-compose logs -f order-service

# Check container status
docker-compose ps

# Verify registry images
curl http://localhost:5000/v2/_catalog

# Test service health
curl http://localhost:8088/api/orders/health

# Check OTEL collector health
curl http://localhost:13133/
```
