# Engineering Specification

## From Commit to Culprit: An Elastic Observability Workshop

**Version:** 1.0
**Last Updated:** December 2024

---

## Deployment Targets

This workshop supports two deployment environments. Both use Elastic Cloud Serverless because Workflows (used for automated rollback) is only available on Serverless.

### Instruqt Environment (Primary)

- **Platform:** Elastic Cloud Serverless (pre-provisioned per participant)
- **Agent Builder:** Available and fully functional
- **ML Pre-training:** Baseline data generated during setup
- **Webhook Connectivity:** Instruqt service exposure provides public URL
- **All Challenges:** Fully supported (1-4)

### Local Development (Recommended)

- **Platform:** Elastic Cloud Serverless (developer's own project)
- **Agent Builder:** Available and fully functional
- **ML Pre-training:** Optional (requires manual baseline generation)
- **Webhook Connectivity:** Requires tunnel (e.g., ngrok) for automated rollback from Elastic Cloud
- **All Challenges:** Fully supported (1-4)

### Local Development (start-local) - Limited

- **Platform:** Local Elastic stack via `curl -fsSL https://elastic.co/start-local | sh`
- **Limitations:**
  - **Workflows:** NOT available (no automated rollback)
  - **Agent Builder:** NOT available
  - **ML:** Limited functionality
- **Use Case:** Quick testing of service instrumentation and basic APM features only
- **Challenge Support:** Challenges 1-2 partially work. Challenges 3-4 require Serverless features.

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Order Service | Java, Spring Boot | 21, 3.2.x | Primary entry point |
| Inventory Service | Python, FastAPI | 3.11, 0.109.x | Stock management |
| Payment Service | Python, FastAPI | 3.11, 0.109.x | Payment processing |
| Rollback Webhook | Python, FastAPI | 3.11, 0.109.x | Automated remediation |
| Container Runtime | Docker | 24.x | Container execution |
| Orchestration | Docker Compose | 2.x | Multi-container management |
| Local Registry | registry:2 | 2.8.3 | Image storage |
| Telemetry | OTel Collector Contrib | 0.91.0 | OpenTelemetry collection |
| Observability | Elastic Cloud Serverless | Latest | APM, Logs, Metrics |

> **Note:** The OTel Collector version should be updated periodically to stay current with releases.

---

## Service Specifications

### Order Service (Java Spring Boot)

**Purpose:** Entry point for the e-commerce flow. Receives order requests, validates inventory, processes payment, and returns confirmation.

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/orders | Create a new order |
| GET | /api/orders/{id} | Get order by ID |
| GET | /api/orders/health | Health check |
| GET | /api/orders/ready | Readiness check |

**Bad Code Implementation (v1.1-bad):**

```java
@PostMapping("/api/orders")
public ResponseEntity<OrderResponse> createOrder(@RequestBody OrderRequest request) {
    // Normal order processing...

    // THE BUG: Jordan's detailed trace logging
    Span loggingSpan = tracer.spanBuilder("detailed-trace-logging")
        .setAttribute("logging.type", "detailed-trace")
        .setAttribute("logging.author", "jordan.rivera")
        .setAttribute("logging.commit_sha", "a1b2c3d4")
        .setAttribute("logging.pr_number", "PR-1247")
        .setAttribute("logging.delay_ms", 2000)
        .setAttribute("logging.destination", "/var/log/orders/trace.log")
        .startSpan();

    try (Scope scope = loggingSpan.makeCurrent()) {
        log.debug("Writing detailed trace data to disk: 2000ms");
        Thread.sleep(2000);  // THE BUG: Synchronous file I/O
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    } finally {
        loggingSpan.end();
    }

    // Continue with order processing...
}
```

**Workshop Scope Note:** The main workshop (Challenges 1-4) only requires Order Service to have good and bad versions. `Dockerfile.bad` is only needed for Order Service in the core workshop. Inventory and Payment bad versions (described in BONUS-CHALLENGES.md) are optional extensions for self-guided learning after the main workshop.

**Project Structure:**

```
order-service/
├── Dockerfile
├── Dockerfile.bad
├── pom.xml
└── src/
    ├── main/java/com/novamart/order/
    │   ├── OrderServiceApplication.java
    │   ├── controller/OrderController.java
    │   ├── service/
    │   │   ├── OrderService.java
    │   │   ├── InventoryClient.java
    │   │   └── PaymentClient.java
    │   ├── model/
    │   └── config/TelemetryConfig.java
    └── test/java/com/novamart/order/
```

---

### Inventory Service (Python FastAPI)

**Purpose:** Manages product inventory. Checks stock availability and reserves items.

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/inventory/check | Check stock availability |
| POST | /api/inventory/reserve | Reserve items for order |
| GET | /health | Health check |
| GET | /ready | Readiness check |

**In-Memory Data:**
```python
INVENTORY = {
    "WIDGET-001": {"name": "Standard Widget", "stock": 1000, "price": 29.99},
    "WIDGET-002": {"name": "Premium Widget", "stock": 500, "price": 49.99},
    "GADGET-042": {"name": "Super Gadget", "stock": 250, "price": 82.52},
}
```

---

### Payment Service (Python FastAPI)

**Purpose:** Processes payments. Validates payment methods and charges customers.

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/payments | Process a payment |
| GET | /api/payments/{id} | Get payment status |
| GET | /health | Health check |
| GET | /ready | Readiness check |

---

### Rollback Webhook Service

**Purpose:** Receives webhook calls from Elastic Workflows and executes rollback commands.

```python
@app.post("/rollback")
async def trigger_rollback(request: RollbackRequest):
    logger.info(f"Rollback requested for {request.service}")
    
    update_env_version(request.service, request.target_version)
    
    result = subprocess.run(
        ["docker-compose", "-f", "/app/infra/docker-compose.yml", 
         "up", "-d", "--no-deps", request.service],
        capture_output=True
    )
    
    return {"status": "ROLLBACK_INITIATED", ...}
```

---

## Telemetry Configuration

### EDOT Collector

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
  resource:
    attributes:
      - key: deployment.environment
        value: ${ENVIRONMENT}
        action: upsert

exporters:
  otlp/elastic:
    endpoint: ${ELASTIC_ENDPOINT}
    headers:
      Authorization: "ApiKey ${ELASTIC_API_KEY}"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [otlp/elastic]
    metrics:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [otlp/elastic]
    logs:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [otlp/elastic]
```

### Log Correlation

**Java (logback):**
```xml
<pattern>%d{HH:mm:ss.SSS} %-5level [%X{trace_id}] %msg [%logger{36}:%line]%n</pattern>
```

**Python:**
```python
format='%(asctime)s %(levelname)s [%(trace_id)s] %(message)s [%(filename)s:%(lineno)d]'
```

---

## Scripts

### deploy.sh

Simulates CI/CD deployment:
1. Updates .env with new version
2. Pulls image from local registry
3. Runs docker-compose up
4. Sends deployment annotation to Elastic APM
5. Performs health check

#### Deployment Annotations

Deployment annotations appear as vertical lines on APM charts, helping correlate deployments with metric changes. The deploy.sh script sends annotations via the APM annotation API:

```bash
curl -X POST "${KIBANA_URL}/api/apm/services/${SERVICE}/annotation" \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d '{
    "@timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "service": {
      "name": "'${SERVICE}'",
      "version": "'${VERSION}'"
    },
    "message": "Deployed '${VERSION}' by '${AUTHOR}'",
    "tags": ["deployment", "'${ENVIRONMENT}'"]
  }'
```

### generate-baseline.sh

Generates synthetic baseline traffic for ML pre-training:
1. Sends 10 minutes of "good" traffic with backdated timestamps
2. Populates historical data so ML job has a baseline
3. Runs automatically during Instruqt setup before participants start
4. Optional for local development

### load-generator.sh

Simple bash curl loop that sends random orders at 2-5 requests per second.

### setup-elastic.sh

Provisions all Elastic assets via Kibana API:
- ML anomaly detection job
- SLOs (latency and availability)
- Alert rules (threshold and SLO burn rate)
- Webhook connector (uses WEBHOOK_PUBLIC_URL environment variable)
- Agent Builder tools and agent
- Workshop dashboard

### demo-mode.sh

Fast-forward script for demos and testing:
1. Deploys bad code
2. Waits for alert to fire
3. Captures key timestamps and URLs
4. Useful for facilitator demonstrations and CI testing

---

## Docker Compose

```yaml
services:
  order-service:
    image: ${REGISTRY}/order-service:${ORDER_SERVICE_VERSION:-v1.0}
    ports: ["8088:8080"]
    environment:
      - OTEL_SERVICE_NAME=order-service
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
    depends_on: [otel-collector, inventory-service, payment-service]

  inventory-service:
    image: ${REGISTRY}/inventory-service:${INVENTORY_SERVICE_VERSION:-v1.0}
    ports: ["8081:8081"]

  payment-service:
    image: ${REGISTRY}/payment-service:${PAYMENT_SERVICE_VERSION:-v1.0}
    ports: ["8082:8082"]

  rollback-webhook:
    image: ${REGISTRY}/rollback-webhook:v1.0
    ports: ["9000:9000"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.91.0
    command: ["--config=/etc/otel-collector-config.yaml"]
    ports: ["4317:4317", "4318:4318"]

  registry:
    image: registry:2.8.3
    ports: ["5000:5000"]
```

---

## Testing Strategy

### Unit Tests
- Order Service: JUnit 5
- Python Services: pytest

### Telemetry Tests
- Verify trace propagation across services
- Verify log correlation with trace IDs

### E2E Scenario Tests
- Full incident detection and remediation flow
- Deploy bad code, wait for alert, verify rollback

---

## Environment Configuration

### .env.local (Local Development with Serverless)

```bash
# Environment detection
ENVIRONMENT=local

# Elastic Cloud Serverless connection (your own project)
ELASTIC_ENDPOINT=https://your-project.es.us-east-1.aws.elastic.cloud:443
ELASTIC_API_KEY=your-base64-encoded-api-key
KIBANA_URL=https://your-project.kb.us-east-1.aws.elastic.cloud

# Webhook URL (use ngrok or similar for automated rollback)
# Run: ngrok http 9000
# Then set: WEBHOOK_PUBLIC_URL=https://abc123.ngrok.io
WEBHOOK_PUBLIC_URL=

# Container registry (local)
REGISTRY=localhost:5000

# Service versions
ORDER_SERVICE_VERSION=v1.0
INVENTORY_SERVICE_VERSION=v1.0
PAYMENT_SERVICE_VERSION=v1.0

# Business constants
AVERAGE_ORDER_VALUE=47.50
```

### .env.start-local (Optional - Limited Features)

```bash
# Environment detection
ENVIRONMENT=local

# Elastic connection (from start-local)
# Note: Workflows and Agent Builder are NOT available with start-local
ELASTIC_ENDPOINT=https://localhost:9200
ELASTIC_API_KEY=your-local-api-key
KIBANA_URL=http://localhost:5601

# Container registry (local)
REGISTRY=localhost:5000

# Service versions
ORDER_SERVICE_VERSION=v1.0
INVENTORY_SERVICE_VERSION=v1.0
PAYMENT_SERVICE_VERSION=v1.0

# Business constants
AVERAGE_ORDER_VALUE=47.50
```

### .env.instruqt (Instruqt Environment)

```bash
# Environment detection
ENVIRONMENT=instruqt

# Elastic Cloud Serverless connection (provided by Instruqt setup)
ELASTIC_ENDPOINT=https://your-deployment.es.us-east-1.aws.elastic.cloud:443
ELASTIC_API_KEY=your-base64-encoded-api-key
KIBANA_URL=https://your-deployment.kb.us-east-1.aws.elastic.cloud

# Webhook URL (generated by Instruqt service exposure)
WEBHOOK_PUBLIC_URL=https://track-abc123-9000.instruqt.io

# Container registry (local)
REGISTRY=localhost:5000

# Service versions
ORDER_SERVICE_VERSION=v1.0
INVENTORY_SERVICE_VERSION=v1.0
PAYMENT_SERVICE_VERSION=v1.0

# Business constants
AVERAGE_ORDER_VALUE=47.50
```

---

## Baseline Data Generation

For the 2-hour workshop, SLOs and threshold alerts are the primary detection mechanisms. ML anomaly detection is a supplementary observation, not critical path.

### ML Pre-training Approach

During Instruqt setup, `generate-baseline.sh` runs before participants start:

1. **Generate synthetic traffic:** Send 10 minutes of "good" traffic patterns
2. **Backdate timestamps:** Ensure data appears as historical for ML baseline
3. **Train ML job:** The ML anomaly detection job trains on this historical data
4. **Result:** When participants begin, a baseline exists for anomaly comparison

For local development, baseline generation is optional. Participants can run `generate-baseline.sh` manually if they want to test ML features.

---

## Agent Builder Tools

Agent Builder tools are configured via the Kibana Agent Builder API. Each tool consists of:
- **Name:** Unique identifier for the tool
- **Description:** What the tool does (used by the LLM for tool selection)
- **Parameters:** Input parameters with descriptions
- **Query template:** Elasticsearch query with parameter placeholders
- **Instructions:** LLM instructions for interpreting results

Tools are stored as saved objects and exported as JSON files in `elastic-assets/agent-builder/tools/`. The `setup-elastic.sh` script POSTs these JSON files to the Agent Builder API.

### Example Tool: Business Impact Calculator

```json
{
  "name": "business-impact-calculator",
  "description": "Calculate revenue impact of service degradation",
  "parameters": {
    "start_time": "ISO timestamp for incident start",
    "end_time": "ISO timestamp for incident end",
    "service": "Service name to analyze"
  },
  "query_template": {
    "index": "traces-apm*",
    "body": {
      "query": {
        "bool": {
          "filter": [
            {"term": {"service.name": "{{service}}"}},
            {"range": {"@timestamp": {"gte": "{{start_time}}", "lte": "{{end_time}}"}}}
          ]
        }
      },
      "aggs": {
        "failed_transactions": {
          "filter": {"term": {"event.outcome": "failure"}}
        }
      }
    }
  },
  "instructions": "Multiply failed_transactions by 47.50 to calculate revenue impact in dollars."
}
```

### All Agent Builder Tools

| Tool | Purpose |
|------|---------|
| apm-latency-comparison | Compare latency between versions or time periods |
| deployment-timeline | Show deployment history with metadata |
| error-pattern-analysis | Surface error patterns after deployments |
| incident-timeline | Create chronological incident summary |
| service-health-snapshot | Current health across all services |
| slo-status-budget | SLO status and error budget remaining |
| business-impact-calculator | Calculate revenue impact of degradation |
