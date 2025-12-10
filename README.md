# From Commit to Culprit

**An Elastic Observability Mystery Workshop**

[![Elastic](https://img.shields.io/badge/Elastic-00BFB3?style=for-the-badge&logo=elastic&logoColor=white)](https://www.elastic.co)
[![Instruqt](https://img.shields.io/badge/Instruqt-Workshop-blue?style=for-the-badge)](https://instruqt.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-green?style=for-the-badge)](LICENSE)

---

## The Story

> *It is 2:47 PM on a Friday. The Order Service team just deployed version 1.1 with a "minor performance optimization." Within minutes, customers start complaining about slow checkouts. The on-call SRE's phone buzzes. An alert fires. Something is wrong, but what?*
>
> *Your mission: Use Elastic Observability to trace the problem from symptom to source, identify the guilty commit, and trigger an automated rollback before the weekend is ruined.*

---

## Workshop Overview

| Attribute | Details |
|-----------|---------|
| **Duration** | 2 hours |
| **Audience** | DevOps Engineers, SREs |
| **Elastic Experience** | Basic (familiarity with Kibana helpful) |
| **Format** | Hands-on labs with guided narrative |

### What You Will Learn

By the end of this workshop, you will be able to:

1. **Instrument microservices** using Elastic's Distribution of OpenTelemetry (EDOT) for traces, logs, and metrics
2. **Correlate telemetry signals** by navigating between traces, logs, and metrics to find root cause
3. **Configure and interpret SLOs** to measure service health and error budgets
4. **Use ML anomaly detection** to identify behavioral changes
5. **Automate incident remediation** using Elastic Workflows
6. **Calculate business impact** of service degradation in real-time
7. **Use Agent Builder** to investigate incidents conversationally

---

## Architecture

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

---

## Challenges

### Challenge 1: Setup and Baseline (20 min)
> *"Before we begin our investigation, let us make sure our instruments are calibrated."*

- Verify environment connectivity
- Explore the running application
- Generate baseline traffic
- Tour APM, Logs, Metrics, and SLOs in Kibana

### Challenge 2: Deploy and Detect (30 min)
> *"The Order Service team ships a 'performance optimization.' Within minutes, your phone buzzes."*

- Deploy the bad version using `deploy.sh`
- Observe the SLO burn rate spike
- Watch the alerts fire
- See the business impact mount in real-time

### Challenge 3: Investigate and Remediate (25 min)
> *"You know something is wrong. Now find the culprit and fix it."*

- Deep dive into slow traces
- Correlate with logs (filter by trace ID)
- Use APM Correlations to identify the issue
- Find the exact code causing the problem
- Watch the automated rollback restore service

### Challenge 4: Learn and Prevent (15 min)
> *"The incident is over. What did we learn?"*

- Use Agent Builder to query the incident
- Create a Case to document findings
- Review total business impact
- Discuss best practices

---

## Quick Start (Local Development)

### Prerequisites

- Docker and Docker Compose
- curl and bash
- Elastic Cloud Serverless project (required for Workflows and Agent Builder)
- ngrok or similar tunnel service (for webhook connectivity)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/from-commit-to-culprit.git
cd from-commit-to-culprit

# Copy and configure environment
cp infra/.env.example infra/.env
# Edit .env with your Elastic Cloud Serverless endpoint and API key

# Start ngrok tunnel for webhook connectivity (in separate terminal)
ngrok http 9000
# Copy the public URL and add to .env as WEBHOOK_PUBLIC_URL

# Build images and start services
./scripts/build-images.sh
docker-compose -f infra/docker-compose.yml up -d

# Provision Elastic assets
./scripts/setup-elastic.sh

# Generate traffic
./scripts/load-generator.sh
```

> **Note:** This workshop requires Elastic Cloud Serverless for full functionality. Workflows (automated rollback) and Agent Builder are only available on Serverless.

### Simulate the Incident

```bash
# Deploy the bad code
./scripts/deploy.sh order-service v1.1-bad

# Watch in Kibana as:
# 1. Latency spikes
# 2. SLO burn rate increases
# 3. Alert fires
# 4. Workflow triggers rollback
# 5. Service recovers automatically
```

---

## Key Features Demonstrated

| Feature | Description |
|---------|-------------|
| **EDOT** | Elastic Distribution of OpenTelemetry for auto-instrumentation |
| **Distributed Tracing** | Follow requests across microservices |
| **Log Correlation** | Filter logs by trace ID |
| **SLOs** | Service Level Objectives with error budgets |
| **ML Anomaly Detection** | Automatic baseline learning and anomaly detection |
| **APM Correlations** | Automatically identify what is different about slow requests |
| **Workflows** | Automated remediation via webhooks |
| **Agent Builder** | AI-powered conversational investigation |
| **Business Impact** | Real-time revenue impact visualization |

---

## Documentation

| Document | Description |
|----------|-------------|
| [PRD](docs/PRD.md) | Product Requirements Document |
| [Design](docs/DESIGN.md) | Design Document with UX flows |
| [Engineering](docs/ENGINEERING.md) | Engineering Specification |
| [Architecture](docs/ARCHITECTURE.md) | Detailed architecture documentation |
| [Characters](docs/CHARACTERS.md) | Character profiles and narrative guidelines |
| [Bonus Challenges](docs/BONUS-CHALLENGES.md) | Extended scenarios for self-guided learning |

---

## Participant Takeaways

After completing the workshop, participants receive:

1. **This GitHub repository** - Clone and run locally
2. **SRE Quick Reference** - One-page guide to investigation patterns
3. **Kibana Dashboard** - Export for your own environment
4. **Agent Builder Config** - Import the investigation agent

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

### Running Tests

```bash
# Unit tests
./scripts/run-tests.sh unit

# Integration tests
./scripts/run-tests.sh integration

# End-to-end tests
./scripts/run-tests.sh e2e
```

---

## Support

- **Workshop Issues:** Open an issue in this repository
- **Elastic Questions:** [Elastic Community](https://discuss.elastic.co/)
- **Instruqt Issues:** Contact your Elastic representative

---

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Happy investigating!</strong><br>
  <em>"From Commit to Culprit" - An Elastic Observability Workshop</em>
</p>
