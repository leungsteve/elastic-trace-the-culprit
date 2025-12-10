# From Commit to Culprit: An Elastic Observability Workshop

**Teach SREs and DevOps Engineers to investigate production incidents using Elastic Observability**

[![Elastic](https://img.shields.io/badge/Elastic-00BFB3?style=for-the-badge&logo=elastic&logoColor=white)](https://www.elastic.co)
[![Instruqt](https://img.shields.io/badge/Instruqt-Workshop-blue?style=for-the-badge)](https://instruqt.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-green?style=for-the-badge)](LICENSE)

---

## Overview

This hands-on workshop teaches DevOps engineers and SREs how to use Elastic Observability to investigate production incidents, trace problems to their source code, and implement automated remediation.

**The Scenario:** It's Friday afternoon at NovaMart, a mid-size e-commerce company. The Order Service team just deployed version 1.1 with a "minor performance optimization." Within minutes, customers complain about slow checkouts. Your mission as the on-call SRE is to use Elastic Observability to trace the problem from symptom to source, identify the guilty commit, and trigger an automated rollback before the weekend is ruined.

**Duration:** 2 hours
**Format:** Hands-on Instruqt workshop with guided narrative
**Experience Level:** Basic (familiarity with Kibana helpful)

---

## What You Will Learn

By the end of this workshop, you will be able to:

1. **Instrument microservices** using Elastic Distribution of OpenTelemetry (EDOT) for traces, logs, and metrics
2. **Correlate telemetry signals** by navigating between traces, logs, and metrics to find root cause
3. **Configure and interpret SLOs** to measure service health and error budgets
4. **Use ML anomaly detection** to identify behavioral changes in service performance
5. **Automate incident remediation** using Elastic Workflows
6. **Calculate business impact** of service degradation in real-time
7. **Use Agent Builder** to investigate incidents conversationally with AI

---

## Architecture Overview

This workshop uses a microservices architecture representing a simplified e-commerce platform:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WORKSHOP ENVIRONMENT                            │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │   Order     │  │  Inventory  │  │   Payment   │                     │
│  │  Service    │──│   Service   │──│   Service   │                     │
│  │  (Java)     │  │  (Python)   │  │  (Python)   │                     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                     │
│         └────────────────┼────────────────┘                             │
│                          │                                              │
│                   ┌──────▼──────┐                                       │
│                   │    EDOT     │                                       │
│                   │  Collector  │                                       │
│                   └──────┬──────┘                                       │
│                          │                                              │
└──────────────────────────┼──────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Elastic Cloud         │
              │  Serverless            │
              │  ┌──────────────────┐  │
              │  │ APM / Traces     │  │
              │  │ Logs / Metrics   │  │
              │  │ SLOs             │  │
              │  │ ML Anomaly       │  │
              │  │ Workflows        │  │
              │  │ Agent Builder    │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

### Microservices

| Service | Technology | Purpose |
|---------|------------|---------|
| **Order Service** | Java 21, Spring Boot 3.x | Entry point for e-commerce flow. Receives orders, validates inventory, processes payments |
| **Inventory Service** | Python 3.11, FastAPI | Manages product inventory, checks stock availability, reserves items |
| **Payment Service** | Python 3.11, FastAPI | Processes payments, validates payment methods, charges customers |
| **Rollback Webhook** | Python 3.11, FastAPI | Receives webhook calls from Elastic Workflows and executes rollback commands |

All services are stateless with in-memory data structures and instrumented using Elastic Distribution of OpenTelemetry (EDOT) to emit traces, logs, and metrics.

---

## Prerequisites

To run this workshop locally, you need:

- **Docker** (version 24.x or later) and **Docker Compose** (version 2.x or later)
- **Elastic Cloud Serverless account** (required for Workflows and Agent Builder features)
  - Create a free trial at [cloud.elastic.co](https://cloud.elastic.co)
  - Note: Local Elastic stack (`start-local`) has limited functionality
- **curl and bash** for running scripts
- **ngrok or similar tunnel service** (optional, for webhook connectivity in local development)
  - Alternative: Use `auto-rollback-monitor.sh` script to simulate automated rollback without tunnel

---

## Quick Start Guide

### 1. Clone the Repository

```bash
git clone https://github.com/elastic/elastic-trace-the-culprit.git
cd elastic-trace-the-culprit
```

### 2. Configure Environment with Elastic Credentials

```bash
# Copy the example environment file
cp infra/.env.example infra/.env

# Edit .env and add your Elastic Cloud Serverless credentials
# Required variables:
#   ELASTIC_ENDPOINT=https://your-project.es.us-east-1.aws.elastic.cloud:443
#   ELASTIC_API_KEY=your-base64-encoded-api-key
#   KIBANA_URL=https://your-project.kb.us-east-1.aws.elastic.cloud
```

**Getting Elastic Credentials:**

1. Log in to [Elastic Cloud](https://cloud.elastic.co)
2. Create a new Serverless Observability project (or use an existing one)
3. Navigate to **Management > API Keys** to create an API key
4. Copy the endpoint URLs from your deployment overview

### 3. Build Docker Images

```bash
# Build all service images and push to local registry
./scripts/build-images.sh
```

This script will:
- Start a local Docker registry on port 5000
- Build images for all services (order, inventory, payment, rollback-webhook)
- Build both v1.0 (good) and v1.1-bad (with latency bug) versions of Order Service
- Push all images to the local registry

### 4. Start Services

```bash
# Start all services using Docker Compose
docker-compose -f infra/docker-compose.yml up -d

# Verify services are running
docker-compose -f infra/docker-compose.yml ps

# Check service health
./scripts/health-check.sh
```

Services will be available at:
- Order Service: http://localhost:8088
- Inventory Service: http://localhost:8081
- Payment Service: http://localhost:8082
- Rollback Webhook: http://localhost:9000

### 5. Provision Elastic Assets

```bash
# Set up SLOs, alerts, workflows, Agent Builder tools, and dashboards
./scripts/setup-elastic.sh
```

This script provisions:
- SLOs for latency and availability (1-hour rolling windows)
- Alert rules (threshold and SLO burn rate)
- Webhook connector for automated rollback
- Agent Builder tools (7 custom investigation tools)
- Workshop overview dashboard

### 6. Generate Traffic

```bash
# Start the load generator to create baseline traffic
./scripts/load-generator.sh

# The script will send random orders at 2-5 requests per second
# Press Ctrl+C to stop when ready
```

---

## Demo Flow

### Step 1: Baseline Monitoring

With services running and traffic flowing, explore Kibana to establish a healthy baseline:

1. Open Kibana at your KIBANA_URL
2. Navigate to **Observability > APM** to see service map and transaction traces
3. Check **Observability > SLOs** to view current SLO status (should be green)
4. View **Observability > Logs** to see correlated log entries
5. Open the **Workshop Overview** dashboard for a unified view

### Step 2: Deploy Bad Version

Simulate a deployment that introduces a performance regression:

```bash
# Deploy v1.1-bad which includes a 2-second sleep bug
./scripts/deploy.sh order-service v1.1-bad
```

The deploy script will:
- Update the ORDER_SERVICE_VERSION in .env to v1.1-bad
- Pull the bad image from the local registry
- Restart the order-service container
- Send a deployment annotation to Elastic APM (visible as vertical line on charts)
- Verify service health

### Step 3: Watch Latency Spike

Return to Kibana and observe the incident unfold in real-time:

1. **APM Service Map:** Order Service turns yellow/red
2. **Transaction Latency:** Average latency jumps from ~200ms to ~2200ms
3. **SLO Dashboard:** Burn rate spikes, error budget depletes rapidly
4. **Alerts:** Threshold alert fires within 1-2 minutes
5. **Business Impact:** Calculate revenue impact (failed orders × $47.50 average order value)

### Step 4: Investigate Root Cause

Use Elastic Observability to identify the exact cause:

1. **Distributed Tracing:**
   - Click on a slow transaction in APM
   - Examine the trace waterfall
   - Notice the new "detailed-trace-logging" span taking 2000ms

2. **Trace Metadata:**
   - Click on the suspicious span
   - View span attributes revealing:
     - `logging.author: jordan.rivera`
     - `logging.commit_sha: a1b2c3d4`
     - `logging.pr_number: PR-1247`
     - `logging.delay_ms: 2000`

3. **Log Correlation:**
   - Copy the trace ID from the slow transaction
   - Navigate to Logs and filter by trace ID
   - See correlated log: "Writing detailed trace data to disk: 2000ms"
   - Log entry includes file name and line number

### Step 5: Auto-Rollback

Watch the automated remediation restore service health:

**Option A: Using Elastic Workflows (requires ngrok tunnel)**

If you configured `WEBHOOK_PUBLIC_URL` in .env:
- SLO burn rate alert triggers automatically
- Elastic Workflows calls the rollback-webhook service
- Webhook updates .env and restarts order-service with v1.0
- Service latency returns to normal within seconds

**Option B: Using Local Monitor Script (no tunnel required)**

```bash
# In a separate terminal, start the auto-rollback monitor
./scripts/auto-rollback-monitor.sh

# The script will:
# - Poll order-service latency every 5 seconds
# - Trigger rollback webhook when latency exceeds 1000ms for 2 consecutive checks
# - Automatically restore service to v1.0
```

Watch in Kibana as:
- Latency returns to baseline (~200ms)
- SLO burn rate decreases
- Service health turns green
- Deployment annotation marks the rollback event

### Step 6: Post-Incident Analysis with Agent Builder

Use conversational AI to analyze the incident:

1. Navigate to **Observability > Agent Builder** in Kibana
2. Select the "Incident Investigator" agent
3. Ask questions like:
   - "What caused the latency spike at 2:47 PM?"
   - "Show me the deployment timeline for order-service"
   - "Calculate the business impact of this incident"
   - "Compare latency before and after the deployment"
4. The agent uses 7 custom tools to query APM data and provide insights

---

## Workshop Challenges

The Instruqt workshop consists of 4 hands-on challenges:

| Challenge | Duration | Focus |
|-----------|----------|-------|
| **1. Setup and Baseline** | 20 min | Environment verification, explore healthy state, understand SLOs |
| **2. Deploy and Detect** | 30 min | Deploy bad code, observe alerts fire, measure business impact |
| **3. Investigate and Remediate** | 25 min | Trace investigation, log correlation, see automated rollback |
| **4. Learn and Prevent** | 15 min | Agent Builder analysis, create incident Case, discuss best practices |

Each challenge includes:
- **assignment.md:** Step-by-step instructions with narrative context
- **setup.sh:** Automated environment preparation
- **check.sh:** Validation scripts to verify completion
- **solve.sh:** Solution scripts for facilitator demonstrations

---

## Key Features Demonstrated

| Feature | Description |
|---------|-------------|
| **EDOT** | Elastic Distribution of OpenTelemetry for auto-instrumentation of Java and Python services |
| **Distributed Tracing** | Follow requests across microservices with trace propagation and waterfall visualization |
| **Log Correlation** | Filter logs by trace ID to see exactly what happened during a slow transaction |
| **Custom Spans** | Add attribution metadata (author, commit SHA, PR number) to spans for rapid root cause identification |
| **SLOs** | Service Level Objectives with 1-hour rolling windows and error budget tracking |
| **SLO Burn Rate Alerts** | Detect when error budget depletes faster than expected |
| **ML Anomaly Detection** | Automatic baseline learning and anomaly detection for latency patterns |
| **APM Correlations** | Automatically identify what is different about slow requests compared to fast ones |
| **Deployment Annotations** | Vertical lines on charts marking deployments, correlating changes with metrics |
| **Workflows** | Automated remediation via webhooks triggered by SLO burn rate alerts |
| **Agent Builder** | AI-powered conversational investigation with 7 custom tools for incident analysis |
| **Business Impact Calculation** | Real-time revenue impact visualization (failed transactions × average order value) |

---

## Repository Structure

```
elastic-trace-the-culprit/
├── README.md                          # This file
├── CLAUDE.md                          # Development instructions
├── CONTRIBUTING.md                    # Development guidelines
│
├── docs/                              # Detailed documentation
│   ├── PRD.md                         # Product Requirements Document
│   ├── DESIGN.md                      # Design Document with UX flows
│   ├── ENGINEERING.md                 # Engineering Specification
│   ├── ARCHITECTURE.md                # Detailed architecture
│   ├── CHARACTERS.md                  # Character profiles and narrative
│   └── BONUS-CHALLENGES.md            # Extended scenarios
│
├── services/                          # Microservices source code
│   ├── order-service/                 # Java Spring Boot (has v1.0 and v1.1-bad)
│   ├── inventory-service/             # Python FastAPI (v1.0 only)
│   ├── payment-service/               # Python FastAPI (v1.0 only)
│   └── rollback-webhook/              # Python FastAPI webhook service
│
├── infra/                             # Infrastructure configuration
│   ├── docker-compose.yml             # Main compose file
│   ├── docker-compose.registry.yml    # Local registry setup
│   ├── .env.example                   # Example environment file
│   └── otel-collector-config.yaml     # EDOT Collector configuration
│
├── scripts/                           # Automation scripts
│   ├── build-images.sh                # Build all Docker images
│   ├── deploy.sh                      # Deployment simulation script
│   ├── rollback.sh                    # Manual rollback script
│   ├── load-generator.sh              # Traffic generation (bash curl loop)
│   ├── setup-elastic.sh               # Kibana API provisioning
│   ├── health-check.sh                # Service verification
│   ├── generate-baseline.sh           # ML pre-training data generation
│   └── auto-rollback-monitor.sh       # Local Workflows simulation
│
├── elastic-assets/                    # Elastic configuration as code
│   ├── slos/                          # SLO definitions
│   ├── alerts/                        # Alert rule definitions
│   ├── workflows/                     # Workflow connector and actions
│   ├── agent-builder/                 # Agent Builder tools and agent config
│   ├── dashboards/                    # Kibana dashboards
│   ├── ml-jobs/                       # ML anomaly detection jobs
│   └── deployment-metadata/           # Code diff documents for Agent queries
│
├── instruqt/                          # Instruqt workshop configuration
│   ├── track.yml                      # Track definition
│   └── challenges/                    # 4 challenge definitions
│
├── takeaways/                         # Participant resources
│   └── SRE-QUICK-REFERENCE.md         # One-page investigation guide
│
└── tests/                             # Test suites
    ├── unit/                          # Unit tests per service
    ├── integration/                   # Service-to-service tests
    ├── telemetry/                     # Telemetry validation tests
    └── e2e/                           # End-to-end scenario tests
```

---

## Documentation

For detailed technical information, see:

| Document | Description |
|----------|-------------|
| [CLAUDE.md](CLAUDE.md) | Development instructions and technical decisions |
| [docs/PRD.md](docs/PRD.md) | Product Requirements Document |
| [docs/DESIGN.md](docs/DESIGN.md) | Design Document with UX flows |
| [docs/ENGINEERING.md](docs/ENGINEERING.md) | Engineering Specification |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Detailed architecture documentation |
| [docs/CHARACTERS.md](docs/CHARACTERS.md) | Character profiles and narrative guidelines |
| [docs/BONUS-CHALLENGES.md](docs/BONUS-CHALLENGES.md) | Extended scenarios for self-guided learning |

---

## Troubleshooting

### Services Not Starting

```bash
# Check Docker Compose logs
docker-compose -f infra/docker-compose.yml logs

# Restart all services
docker-compose -f infra/docker-compose.yml down
docker-compose -f infra/docker-compose.yml up -d
```

### Elastic Connection Issues

```bash
# Verify environment variables are set correctly
grep -E "ELASTIC_ENDPOINT|ELASTIC_API_KEY|KIBANA_URL" infra/.env

# Test connectivity to Elastic Cloud
curl -H "Authorization: ApiKey ${ELASTIC_API_KEY}" "${ELASTIC_ENDPOINT}/_cluster/health"
```

### No Data in Kibana

```bash
# Verify EDOT Collector is running
docker-compose -f infra/docker-compose.yml logs otel-collector

# Check if services are sending telemetry
curl http://localhost:8088/api/orders/health
```

### Auto-Rollback Not Working

If using Elastic Workflows:
- Verify `WEBHOOK_PUBLIC_URL` is set in .env
- Check ngrok tunnel is running: `ngrok http 9000`
- Test webhook manually: `curl -X POST http://localhost:9000/rollback -H "Content-Type: application/json" -d '{"service":"order-service","target_version":"v1.0"}'`

If using local monitor script:
- Ensure `auto-rollback-monitor.sh` is running
- Check threshold settings: default is 1000ms
- View monitor logs for debugging

---

## Participant Takeaways

After completing the workshop, participants receive:

1. **This GitHub Repository** - Clone and run the entire workshop environment locally
2. **SRE Quick Reference** - One-page guide to investigation patterns ([takeaways/SRE-QUICK-REFERENCE.md](takeaways/SRE-QUICK-REFERENCE.md))
3. **Kibana Dashboard** - Export the Workshop Overview dashboard for your own environment
4. **Agent Builder Configuration** - Import the Incident Investigator agent with 7 custom tools
5. **Deployment Best Practices** - Guidelines for instrumenting services with attribution metadata

---

## Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run telemetry validation tests
pytest tests/telemetry/

# Run end-to-end scenario tests
pytest tests/e2e/
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code style guidelines
- Testing requirements
- Pull request process
- Development priorities

---

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

---

## Support and Resources

- **Workshop Issues:** [Open an issue](https://github.com/elastic/elastic-trace-the-culprit/issues) in this repository
- **Elastic Documentation:**
  - [Elastic Observability](https://www.elastic.co/docs/solutions/observability)
  - [EDOT Documentation](https://www.elastic.co/docs/solutions/observability/apm/opentelemetry)
  - [Agent Builder](https://www.elastic.co/docs/solutions/search/elastic-agent-builder)
  - [SLOs](https://www.elastic.co/docs/solutions/observability/incident-management/service-level-objectives-slos)
  - [Workflows](https://www.elastic.co/docs/solutions/observability/incident-management/alerting)
- **Community:** [Elastic Community Forums](https://discuss.elastic.co/)
- **Instruqt Issues:** Contact your Elastic representative

---

<p align="center">
  <strong>Happy investigating!</strong><br>
  <em>"From Commit to Culprit: An Elastic Observability Workshop"</em><br>
  <sub>Trace the problem. Find the commit. Save the weekend.</sub>
</p>
