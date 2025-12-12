# Claude Code Instructions

## Project Overview

**"From Commit to Culprit: An Observability Mystery"** is an Instruqt workshop that teaches DevOps engineers and SREs how to use Elastic Observability to investigate production incidents, trace problems to their source code, and implement automated remediation.

### Incident Response Lifecycle

The workshop teaches the **complete incident response lifecycle**:

```
DETECT  ──►  INVESTIGATE  ──►  REMEDIATE  ──►  LEARN
  │              │                │              │
  ▼              ▼                ▼              ▼
Challenge 2   Challenge 3    Challenge 3    Challenge 4
(Alerts)      (APM/Traces)   (Workflows)   (Agent Builder)
```

| Phase | Elastic Features | Purpose |
|-------|------------------|---------|
| **Detect** | SLOs, Alerts, ML Anomaly | Proactive detection before customers complain |
| **Investigate** | APM Correlations, Tracing, Log Correlation | Root cause analysis with correlated signals |
| **Remediate** | Workflows, Webhook Connector | Automated rollback to minimize MTTR |
| **Learn** | Agent Builder, Cases | Post-incident analysis and prevention |

Agent Builder is the **finale** (Challenge 4) where participants use conversational AI to synthesize incident data, calculate business impact, and document lessons learned.

## Repository Structure

```
elastic-trace-the-culprit/
├── claude.md                          # This file - development instructions
├── README.md                          # Workshop overview and quick start
├── CONTRIBUTING.md                    # Development guidelines
│
├── docs/
│   ├── PRD.md                         # Product Requirements Document
│   ├── DESIGN.md                      # Design Document with UX flows
│   ├── ENGINEERING.md                 # Engineering Specification
│   ├── ARCHITECTURE.md                # Detailed architecture
│   ├── CHARACTERS.md                  # Character profiles and narrative
│   └── BONUS-CHALLENGES.md            # Extended scenarios
│
├── services/
│   ├── order-service/                 # Java Spring Boot microservice
│   │   ├── Dockerfile
│   │   ├── Dockerfile.bad             # Builds v1.1-bad image
│   │   ├── pom.xml
│   │   └── src/
│   │       ├── main/java/com/novamart/order/
│   │       └── test/java/com/novamart/order/
│   │
│   ├── inventory-service/             # Python FastAPI microservice
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── src/inventory/
│   │
│   ├── payment-service/               # Python FastAPI microservice
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── src/payment/
│   │
│   └── rollback-webhook/              # Python FastAPI webhook service
│       ├── Dockerfile
│       ├── pyproject.toml
│       └── src/webhook/
│
├── infra/
│   ├── docker-compose.yml             # Main compose file
│   ├── docker-compose.registry.yml    # Local registry setup
│   ├── .env.example                   # Example environment file
│   ├── .env.local                     # Local development config (start-local)
│   ├── .env.instruqt                  # Instruqt environment config
│   ├── .env.serverless                # Elastic Cloud Serverless config
│   └── otel-collector-config.yaml     # OpenTelemetry Collector configuration
│
├── scripts/
│   ├── deploy.sh                      # Deployment simulation script
│   ├── rollback.sh                    # Manual rollback script
│   ├── load-generator.sh              # Bash curl loop for traffic
│   ├── setup-elastic.sh               # Kibana API provisioning
│   ├── setup-registry.sh              # Local registry setup
│   ├── build-images.sh                # Build all Docker images
│   ├── health-check.sh                # Service verification
│   └── auto-rollback-monitor.sh       # Local Workflows simulation
│
├── elastic-assets/
│   ├── ml-jobs/
│   │   └── apm-latency-anomaly.json
│   ├── alerts/
│   │   ├── latency-threshold.json
│   │   └── slo-burn-rate.json
│   ├── slos/
│   │   ├── order-latency.json
│   │   └── order-availability.json
│   ├── workflows/
│   │   ├── webhook-connector.json
│   │   └── auto-rollback-action.json
│   ├── agent-builder/
│   │   ├── agent.json
│   │   └── tools/
│   │       ├── apm-latency-comparison.json
│   │       ├── deployment-timeline.json
│   │       ├── error-pattern-analysis.json
│   │       ├── incident-timeline.json
│   │       ├── service-health-snapshot.json
│   │       ├── slo-status-budget.json
│   │       └── business-impact-calculator.json
│   ├── dashboards/
│   │   └── workshop-overview.ndjson
│   ├── deployment-metadata/
│   │   └── v1.1-bad-changes.json
│   └── cases/
│       └── incident-template.json
│
├── instruqt/
│   ├── track.yml                      # Instruqt track definition
│   ├── config.yml                     # Track configuration
│   └── challenges/
│       ├── 01-setup-and-baseline/
│       │   ├── assignment.md
│       │   ├── setup.sh
│       │   ├── check.sh
│       │   └── solve.sh
│       ├── 02-deploy-and-detect/
│       ├── 03-investigate-and-remediate/
│       └── 04-learn-and-prevent/
│
├── takeaways/
│   └── SRE-QUICK-REFERENCE.md         # Participant reference guide
│
└── tests/
    ├── unit/                          # Unit tests per service
    ├── integration/                   # Service-to-service tests
    ├── telemetry/                     # Telemetry validation tests
    └── e2e/                           # End-to-end scenario tests
```

## Key Technical Decisions

### Sample Application Stack
- **Order Service:** Java 21, Spring Boot 3.x, EDOT Java agent (auto-instrumentation)
- **Inventory Service:** Python 3.11, FastAPI, OpenTelemetry Python distro (auto-instrumentation)
- **Payment Service:** Python 3.11, FastAPI, OpenTelemetry Python distro (auto-instrumentation)
- **All services are stateless** with in-memory data structures

### Telemetry
- **Order Service:** Elastic Distribution of OpenTelemetry (EDOT) Java agent
- **Python Services:** Standard OpenTelemetry Python distro with OTLP exporter
- **Collector:** OpenTelemetry Collector Contrib (sends to Elastic via OTLP)
- All services emit traces, logs, and metrics
- Log correlation via trace ID injection
- Custom spans with attribution metadata (author, commit SHA, PR number)

### Container Strategy
- Local registry (registry:2) on port 5000
- Pre-built images for v1.0 (good) and v1.1-bad (with 2-second sleep)
- deploy.sh swaps image versions via docker-compose

### Elastic Configuration
- Supports three deployment targets: Instruqt, start-local, and Elastic Cloud Serverless
- SLOs with 1-hour rolling windows
- SLO burn rate alert triggers auto-rollback workflow
- Agent Builder with 7 custom tools

### Environment Detection
- `ENVIRONMENT` variable: `instruqt`, `local`, or `serverless`
- Scripts auto-detect environment and configure endpoints accordingly
- Startup banner shows environment, Elastic connection status, version

## Development Guidelines

### Code Style
- **Java:** Follow Google Java Style Guide
- **Python:** Follow PEP 8, use type hints
- **Shell scripts:** Use shellcheck, include error handling
- **All code:** Include comprehensive comments explaining workshop context

### Testing Strategy (TDD)
1. **Unit tests** for each service's business logic
2. **Integration tests** for service-to-service communication
3. **Telemetry tests** verifying trace propagation and log correlation
4. **Infrastructure tests** for container health and .env loading
5. **E2E scenario tests** simulating full participant journey

### Commit Messages
Use conventional commits:
- `feat(order-service): add custom span for detailed trace logging`
- `fix(deploy): correct version extraction from .env`
- `docs(readme): update architecture diagram`
- `test(telemetry): add trace correlation validation`

## Bad Code Implementation

The v1.1-bad version of Order Service includes:

```java
// Jordan's detailed trace logging - wrapped in a span for visibility
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
```

This creates:
1. A visible span in the trace waterfall
2. Attribution metadata (author, commit, PR, destination)
3. A correlated log message with file/line info

## Elastic Asset Provisioning

All Elastic assets are provisioned via Kibana API calls in `setup-elastic.sh`:

1. ML anomaly detection job (pre-trained on synthetic data)
2. SLOs (latency and availability)
3. Threshold alert rule
4. SLO burn rate alert rule
5. Webhook connector for rollback
6. Agent Builder tools (7 tools)
7. Agent Builder agent configuration
8. Workshop dashboard
9. Deployment metadata documents (for code diff queries)

## Narrative Context

### Characters
- **Alex Chen:** On-call SRE, the participant's avatar
- **Jordan Rivera:** Order Service dev who deployed the bad code
- **Sam Patel:** Platform Engineering Manager

### Company
- **NovaMart:** Mid-size e-commerce company
- **Average order value:** $47.50 (for business impact calculations)

### Story Arc
1. Friday afternoon, everything is healthy
2. Jordan deploys v1.1 with "detailed trace logging"
3. Alert fires within minutes
4. Alex investigates using Elastic Observability
5. Workflow triggers automatic rollback
6. Post-incident review with Agent Builder

## Workshop Challenges

| Challenge | Duration | Focus |
|-----------|----------|-------|
| 1. Setup and Baseline | 20 min | Environment verification, explore healthy state |
| 2. Deploy and Detect | 30 min | Deploy bad code, observe alerts fire |
| 3. Investigate and Remediate | 25 min | Trace investigation, see rollback |
| 4. Learn and Prevent | 15 min | Agent Builder, create case, wrap-up |

## Multi-Environment Support

The workshop supports three deployment environments. All scripts and configurations use environment variables for portability.

### Environment Comparison

| Aspect | Instruqt | start-local | Cloud Serverless |
|--------|----------|-------------|------------------|
| Elasticsearch | `http://kubernetes-vm:30920` | `http://localhost:9200` | `https://*.elastic.cloud` |
| Kibana | `http://kubernetes-vm:30002` | `http://localhost:5601` | `https://*.elastic.cloud` |
| APM/OTLP | `http://kubernetes-vm:8200` | `http://localhost:8200` | `https://*.apm.elastic.cloud` |
| TLS | No (HTTP) | No (HTTP) | Yes (HTTPS) |
| Auth | Basic/API Key (pre-set) | Basic (`elastic`/`changeme`) | API Key |
| Workflows | Yes (via ECK) | No | Yes |
| Agent Builder | Yes (via ECK) | No | Yes |

### Environment Configuration Files

- `.env.instruqt` - Sources from pre-set Instruqt environment variables
- `.env.local` - Localhost endpoints for start-local development
- `.env.serverless` - Elastic Cloud Serverless endpoints (user configures)

### Common Environment Variables

```bash
# Environment detection
ENVIRONMENT=instruqt|local|serverless

# Elastic connection (values vary by environment)
ELASTICSEARCH_URL=<endpoint>
KIBANA_URL=<endpoint>
ELASTIC_APM_SERVER_ENDPOINT=<endpoint>

# Authentication (one of these depending on environment)
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=<password>
ELASTICSEARCH_APIKEY=<base64-encoded-api-key>
ELASTIC_APM_SERVER_SECRET=<apm-secret-token>

# Container registry
REGISTRY=localhost:5000

# Service versions
ORDER_SERVICE_VERSION=v1.0
INVENTORY_SERVICE_VERSION=v1.0
PAYMENT_SERVICE_VERSION=v1.0

# Business constants
AVERAGE_ORDER_VALUE=47.50
```

## Instruqt Environment Details

The Instruqt lab uses a two-VM architecture with Elastic running on Kubernetes via ECK.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Instruqt Lab                            │
├─────────────────────────────┬───────────────────────────────────┤
│         host-1              │         kubernetes-vm             │
│   (Workshop Services)       │      (Elastic Stack - ECK)        │
├─────────────────────────────┼───────────────────────────────────┤
│ - Docker runtime            │ - k3s cluster                     │
│ - Workshop repo             │ - ECK operator                    │
│ - OTEL Collector            │ - Elasticsearch 9.x (NodePort)    │
│ - order-service             │ - Kibana 9.x (NodePort + Tab)     │
│ - inventory-service         │ - APM Server (LoadBalancer)       │
│ - payment-service           │ - Fleet Server                    │
│ - rollback-webhook          │                                   │
└─────────────────────────────┴───────────────────────────────────┘
         │                              │
         │     http://kubernetes-vm     │
         └──────────────────────────────┘
```

### Pre-configured Environment Variables (host-1)

Instruqt automatically sets these variables on host-1:

| Variable | Example Value | Purpose |
|----------|---------------|---------|
| `ELASTICSEARCH_URL` | `http://kubernetes-vm:30920` | Elasticsearch endpoint |
| `KIBANA_URL` | `http://kubernetes-vm:30002` | Kibana endpoint |
| `ELASTIC_APM_SERVER_ENDPOINT` | `http://kubernetes-vm:8200` | APM/OTLP endpoint |
| `ELASTICSEARCH_USER` | `elastic` | Auth username |
| `ELASTICSEARCH_PASSWORD` | `<generated>` | Auth password |
| `ELASTICSEARCH_APIKEY` | `<base64>` | API key for programmatic access |
| `ELASTIC_APM_SERVER_SECRET` | `<generated>` | APM secret token |

### Kubernetes Services (kubernetes-vm)

| Service | Type | Port | Access from host-1 |
|---------|------|------|-------------------|
| Elasticsearch | NodePort | 30920 | `http://kubernetes-vm:30920` |
| Kibana | NodePort | 30002 | `http://kubernetes-vm:30002` |
| APM Server | LoadBalancer | 8200 | `http://kubernetes-vm:8200` |
| Fleet Server | NodePort | 30822 | `http://kubernetes-vm:30822` |

### Instruqt Tabs

- **Terminal (host-1)**: Primary workspace for running workshop commands
- **Kibana**: Embedded tab exposing Kibana UI to participants
- **Terminal (kubernetes-vm)**: Optional, for kubectl access if needed

### OTEL Collector Configuration (Instruqt)

```yaml
exporters:
  otlp:
    endpoint: "kubernetes-vm:8200"
    tls:
      insecure: true
    headers:
      Authorization: "Bearer ${ELASTIC_APM_SERVER_SECRET}"
```

### Working Directory

Workshop files should be placed in `/workspace/workshop/` on host-1.

## Git Commit Guidelines

- Never mention Claude, AI, or any AI assistant in commit messages
- Never include phrases like "Generated by", "Created with AI", or similar
- Write commit messages as if a human developer wrote them
- Use conventional commit format: `type(scope): description`
- Examples:
  - `feat(order-service): add custom span for detailed trace logging`
  - `fix(deploy): correct version extraction from .env`
  - `docs(readme): update architecture diagram`
  - `test(telemetry): add trace correlation validation`

## Git Configuration

- Use the repository's configured git user for all commits
- Do not modify git user.name or user.email

## Development Priorities

When implementing this workshop, follow this priority order:

### P0 - Must Have for Workshop

These components are required for the workshop to function:

- **Order Service (Java):** Good version (v1.0) and bad version (v1.1-bad)
- **Inventory Service (Python):** Good version only (v1.0)
- **Payment Service (Python):** Good version only (v1.0)
- **Rollback Webhook Service:** Single version
- **Infrastructure:**
  - docker-compose.yml
  - .env.example, .env.local, .env.instruqt
  - otel-collector-config.yaml
- **Core Scripts:**
  - deploy.sh
  - load-generator.sh
  - setup-elastic.sh
  - health-check.sh
  - build-images.sh
  - generate-baseline.sh
- **Elastic Assets:**
  - SLOs (latency and availability)
  - Alert rules (threshold and SLO burn rate)
  - Webhook connector
  - Workshop dashboard
  - Agent Builder tools and agent configuration
- **Instruqt Challenges:** All 4 challenges with setup.sh, check.sh, solve.sh, assignment.md

### P1 - Should Have

Important but not blocking for initial workshop delivery:

- Unit tests for services
- Telemetry tests (trace propagation validation)
- CONTRIBUTING.md

### P2 - Nice to Have (post-launch)

Enhancements for future iterations:

- Bonus challenge services (Inventory/Payment bad versions)
- E2E scenario tests
- demo-mode.sh fast-forward script

## Ignored Directories

- **deleteme/** - Temporary scratch folder. Ignore all contents and do not read, modify, or reference files in this directory.

## Important Reminders

1. **Never use emdashes.** Use complete sentences instead.
2. **Elastic brand colors:** Use #00BFB3 (teal), #F04E98 (pink), #1BA9F5 (blue)
3. **All services must be stateless** - no database dependencies
4. **Startup banner required** showing environment and connection status
5. **Include commit SHA metadata** in all deployment-related spans and logs
6. **Test everything locally** using Elastic Cloud Serverless before Instruqt testing

## Quick Start for Development

### Option 1: Instruqt Environment

Workshop services run on host-1, Elastic stack is pre-provisioned on kubernetes-vm.

```bash
# On host-1 - environment variables are pre-set
cd /workspace/workshop

# Clone or copy workshop files
git clone https://github.com/your-org/elastic-trace-the-culprit.git .

# Use Instruqt environment config
cp infra/.env.instruqt infra/.env

# Build and start services
./scripts/build-images.sh
docker-compose -f infra/docker-compose.yml up -d

# Provision Elastic assets
./scripts/setup-elastic.sh

# Generate baseline traffic
./scripts/load-generator.sh &

# Deploy bad code (to test the incident)
./scripts/deploy.sh order-service v1.1-bad
```

### Option 2: Elastic Cloud Serverless

Full workshop functionality including Workflows and Agent Builder.

```bash
# Clone the repository
git clone https://github.com/your-org/elastic-trace-the-culprit.git
cd elastic-trace-the-culprit

# Copy and configure serverless environment
cp infra/.env.serverless infra/.env
# Edit .env with your Elastic Cloud Serverless endpoint and API key

# Start ngrok tunnel for webhook connectivity (separate terminal)
ngrok http 9000
# Add the public URL to .env as WEBHOOK_PUBLIC_URL

# Build and start services
./scripts/build-images.sh
docker-compose -f infra/docker-compose.yml up -d

# Provision Elastic assets
./scripts/setup-elastic.sh

# Generate baseline traffic
./scripts/load-generator.sh &

# Deploy bad code (to test the incident)
./scripts/deploy.sh order-service v1.1-bad
```

### Option 3: start-local (Development Only)

Basic instrumentation testing without Workflows or Agent Builder.

```bash
# Clone the repository
git clone https://github.com/your-org/elastic-trace-the-culprit.git
cd elastic-trace-the-culprit

# Use local environment config
cp infra/.env.local infra/.env

# Start local Elastic stack
docker-compose -f infra/docker-compose.yml -f infra/docker-compose.local.yml up -d

# Build and start services
./scripts/build-images.sh
docker-compose -f infra/docker-compose.yml up -d

# Generate baseline traffic
./scripts/load-generator.sh &
```

> **Note:** Workflows (automated rollback) and Agent Builder require Instruqt or Elastic Cloud Serverless. The start-local option is for basic instrumentation testing only.

## References

- [Elastic Observability Docs](https://www.elastic.co/docs/solutions/observability)
- [EDOT Java Agent](https://www.elastic.co/docs/solutions/observability/apm/opentelemetry/java)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
- [Agent Builder Docs](https://www.elastic.co/docs/solutions/search/elastic-agent-builder)
- [SLO Documentation](https://www.elastic.co/docs/solutions/observability/incident-management/service-level-objectives-slos)
- [Workflows (Keep)](https://www.elastic.co/docs/solutions/observability/incident-management/alerting)
