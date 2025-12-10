# Product Requirements Document (PRD)

## From Commit to Culprit: An Elastic Observability Workshop

**Version:** 1.0  
**Last Updated:** December 2024  
**Author:** Solutions Architecture Team  
**Status:** Draft

---

## Executive Summary

"From Commit to Culprit" is a 2-hour hands-on Instruqt workshop that teaches DevOps engineers and SREs how to use Elastic Observability to investigate production incidents. The workshop uses a detective story narrative to guide participants through deploying bad code, detecting the problem via SLOs and alerts, investigating using traces, logs, and metrics, and remediating via automated workflows.

---

## Problem Statement

Organizations adopting microservices architectures struggle with:

1. **Visibility gaps:** Difficulty tracing requests across distributed services
2. **Slow MTTR:** Time wasted searching through disconnected logs and metrics
3. **Reactive operations:** Detecting problems after customers complain
4. **Manual remediation:** Slow rollback processes during incidents
5. **Business disconnect:** Technical metrics not tied to business impact

Elastic Observability addresses these challenges, but practitioners need hands-on experience to understand how the features work together.

---

## Goals and Objectives

### Primary Goals

1. **Demonstrate Elastic's end-to-end observability capabilities** in a realistic scenario
2. **Teach investigation techniques** using trace-to-log correlation and APM features
3. **Showcase automated remediation** via Elastic Workflows
4. **Highlight business value** through SLOs and revenue impact visualization

### Success Metrics

| Metric | Target |
|--------|--------|
| Workshop completion rate | > 85% |
| Participant satisfaction (NPS) | > 50 |
| Feature discovery rate | > 90% discover APM Correlations |
| Post-workshop engagement | > 30% clone the repository |

### Non-Goals

- Teaching Elastic administration or cluster management
- Deep dive into EDOT configuration (covered in separate workshops)
- Production deployment best practices (focus is on investigation)

---

## Target Audience

### Primary Audience

**DevOps Engineers and Site Reliability Engineers (SREs)**

- 2-5 years of experience in operations or platform engineering
- Familiar with containers, CI/CD concepts, and basic observability
- May have used other APM/monitoring tools (Datadog, New Relic, Prometheus)
- Basic familiarity with Kibana helpful but not required

### Audience Characteristics

| Attribute | Profile |
|-----------|---------|
| Technical level | Intermediate |
| Elastic experience | Basic to none |
| Learning style | Hands-on, practical |
| Time availability | 2-hour focused session |
| Motivation | Solve real problems faster |

---

## Requirements

### Functional Requirements

#### FR-1: Environment Setup
- **FR-1.1:** Participants must be able to verify connectivity to Elastic Cloud Serverless
- **FR-1.2:** All three microservices must be running and visible in APM
- **FR-1.3:** Startup banners must display environment detection and connection status
- **FR-1.4:** Health checks must validate service-to-service communication

#### FR-2: Baseline Establishment
- **FR-2.1:** Load generator must produce consistent traffic patterns
- **FR-2.2:** SLOs must show healthy state (green) at workshop start
- **FR-2.3:** ML anomaly detection must have pre-trained baseline
- **FR-2.4:** Business impact dashboard must show $0 initial impact

#### FR-3: Bad Code Deployment
- **FR-3.1:** deploy.sh must swap service versions with single command
- **FR-3.2:** Deployment annotations must appear in APM timeline
- **FR-3.3:** Deployment metadata must include commit SHA, author, and PR number
- **FR-3.4:** Version change must be visible in service.version attribute

#### FR-4: Detection and Alerting
- **FR-4.1:** SLO burn rate must increase within 2 minutes of bad deployment
- **FR-4.2:** SLO burn rate alert must fire within 3 minutes
- **FR-4.3:** Threshold alert must fire when latency exceeds 2 seconds
- **FR-4.4:** ML anomaly must be detected and scored
- **FR-4.5:** Business impact must update in real-time

#### FR-5: Investigation
- **FR-5.1:** Trace waterfall must show custom span with 2-second duration
- **FR-5.2:** Span attributes must include author and commit metadata
- **FR-5.3:** Logs must be filterable by trace ID
- **FR-5.4:** APM Correlations must identify service.version as high-impact field
- **FR-5.5:** Log message must include file and line number information

#### FR-6: Automated Remediation
- **FR-6.1:** Workflow must trigger webhook on alert
- **FR-6.2:** Rollback webhook must execute docker-compose version swap
- **FR-6.3:** Service must recover to healthy state within 2 minutes of rollback
- **FR-6.4:** Alert must transition to "Recovered" state

#### FR-7: Post-Incident Analysis
- **FR-7.1:** Agent Builder must answer questions about the incident
- **FR-7.2:** Agent Builder must retrieve code diff when asked
- **FR-7.3:** Participants must be able to create a Case from the alert
- **FR-7.4:** Business impact total must be visible for the incident window

### Non-Functional Requirements

#### NFR-1: Performance
- **NFR-1.1:** All Kibana pages must load within 3 seconds
- **NFR-1.2:** Search queries must return results within 2 seconds
- **NFR-1.3:** Trace visualization must render within 1 second

#### NFR-2: Reliability
- **NFR-2.1:** Workshop must complete successfully > 95% of attempts
- **NFR-2.2:** Service recovery must occur within 5 minutes of rollback
- **NFR-2.3:** No single point of failure in the application stack

#### NFR-3: Usability
- **NFR-3.1:** All instructions must be copy-paste ready
- **NFR-3.2:** Error messages must include remediation steps
- **NFR-3.3:** Workshop must be completable without facilitator assistance

#### NFR-4: Scalability
- **NFR-4.1:** Support concurrent participants (Instruqt handles isolation)
- **NFR-4.2:** Elastic assets must be provisioned per-participant

---

## User Stories

### Epic 1: Environment Setup

**US-1.1:** As a participant, I want to verify my environment is ready so that I can focus on learning rather than troubleshooting setup.

**Acceptance Criteria:**
- Health check script validates all services
- Kibana displays all three services in APM
- Clear error messages if setup fails

**US-1.2:** As a participant, I want to see what "healthy" looks like so that I can recognize when something is wrong.

**Acceptance Criteria:**
- SLOs show green/healthy status
- Baseline traffic generates visible traces
- Service map shows connected services

### Epic 2: Incident Detection

**US-2.1:** As a participant, I want to deploy a code change so that I can experience a realistic deployment scenario.

**Acceptance Criteria:**
- Single command deploys new version
- Deployment is annotated in APM
- Version change is visible in traces

**US-2.2:** As a participant, I want to see alerts fire automatically so that I understand how Elastic detects problems.

**Acceptance Criteria:**
- Alert fires within 3 minutes of bad deployment
- Alert includes relevant context (service, severity)
- Alert appears in Observability alerts view

**US-2.3:** As a participant, I want to see the business impact so that I can communicate severity to stakeholders.

**Acceptance Criteria:**
- Dashboard shows dollar amount lost
- Impact updates in real-time
- Calculation methodology is visible

### Epic 3: Investigation

**US-3.1:** As a participant, I want to drill down from an alert to the root cause so that I learn the investigation workflow.

**Acceptance Criteria:**
- Can navigate from alert to APM
- Can identify slow span in trace waterfall
- Can see attribution metadata (author, commit)

**US-3.2:** As a participant, I want to correlate traces with logs so that I can see the complete picture.

**Acceptance Criteria:**
- Can filter logs by trace ID
- Log message shows the problematic code behavior
- File and line number are visible

**US-3.3:** As a participant, I want Elastic to tell me what is different about slow requests so that I can find issues faster.

**Acceptance Criteria:**
- APM Correlations identifies service.version
- Impact percentage is displayed
- Correlation is statistically significant

### Epic 4: Remediation

**US-4.1:** As a participant, I want to see automated rollback happen so that I understand the value of Workflows.

**Acceptance Criteria:**
- Workflow triggers automatically on alert
- Rollback executes without manual intervention
- Service recovers to healthy state

**US-4.2:** As a participant, I want to verify the system recovered so that I can confidently close the incident.

**Acceptance Criteria:**
- SLO burn rate returns to normal
- Alert transitions to "Recovered"
- Business impact stops accumulating

### Epic 5: Post-Incident

**US-5.1:** As a participant, I want to ask questions about the incident in natural language so that I can explore Agent Builder capabilities.

**Acceptance Criteria:**
- Agent responds with accurate incident data
- Agent can show code diff
- Agent calculates total business impact

**US-5.2:** As a participant, I want to create a Case for the incident so that I can document my findings.

**Acceptance Criteria:**
- Case can be created from alert
- Relevant context is attached
- Case can be assigned to a user

---

## Feature Specifications

### Feature: SLO-Based Detection

**Description:** Service Level Objectives (SLOs) measure whether the Order Service meets its latency and availability targets. When the error budget burns too quickly, an alert fires.

**SLO Definitions:**

| SLO | Target | Window |
|-----|--------|--------|
| Order Latency | 95% of requests < 500ms | 1 hour rolling |
| Order Availability | 99% success rate | 1 hour rolling |

**Burn Rate Alert:**
- Threshold: 6x sustainable burn rate
- Evaluation window: 5 minutes
- Action: Trigger rollback webhook

### Feature: Business Impact Dashboard

**Description:** A Lens dashboard that calculates and displays the revenue impact of service degradation.

**Calculations:**
- Failed orders = transactions where result = "error"
- Revenue impact = failed orders × $47.50 (average order value)
- Hourly impact = revenue impact × (60 / incident duration in minutes)

**Visualizations:**
- Current orders per hour
- Error rate percentage
- Estimated revenue impact (large number)
- Cumulative impact since incident start

### Feature: Agent Builder Investigation Tools

**Description:** Seven custom tools enable conversational investigation.

| Tool | Purpose |
|------|---------|
| apm-latency-comparison | Compare latency between versions or time periods |
| deployment-timeline | Show deployment history with metadata |
| error-pattern-analysis | Surface error patterns after deployments |
| incident-timeline | Create chronological incident summary |
| service-health-snapshot | Current health across all services |
| slo-status-budget | SLO status and error budget remaining |
| business-impact-calculator | Calculate revenue impact of degradation |

### Feature: Automated Rollback Workflow

**Description:** When the SLO burn rate alert fires, a Workflow sends a webhook to the rollback service, which executes a docker-compose command to restore the previous version.

**Flow:**
1. Alert fires (SLO burn rate > 6x)
2. Workflow evaluates action conditions
3. Webhook POST sent to http://localhost:9000/rollback
4. Rollback service updates docker-compose environment
5. Container restarts with previous version
6. Service recovers, alert resolves

---

## Dependencies

### Technical Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Elastic Cloud Serverless | Latest | Observability platform |
| Docker | 24.x | Container runtime |
| Docker Compose | 2.x | Multi-container orchestration |
| Java | 21 | Order Service runtime |
| Python | 3.11 | Inventory/Payment/Webhook runtime |
| EDOT Collector | Latest | Telemetry collection |

### External Dependencies

| Dependency | Owner | Risk |
|------------|-------|------|
| Instruqt platform | Instruqt | Platform availability |
| Elastic Cloud Serverless | Elastic | Service availability |
| GitHub repository | Solutions team | Repository access |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Elastic Cloud unavailable | Low | High | Document fallback to start-local |
| Instruqt environment issues | Medium | Medium | Provide troubleshooting guide |
| Automation triggers too fast | Medium | Low | Include toggle script to disable/enable |
| ML baseline insufficient | Medium | Medium | Pre-load synthetic "good" data |
| Participants fall behind | Medium | Medium | Include "solve" scripts for each challenge |

---

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Design | 1 week | PRD, Design Doc, Architecture |
| Development | 3 weeks | Services, scripts, Elastic assets |
| Testing | 1 week | Unit, integration, E2E tests |
| Instruqt Integration | 1 week | Track configuration, challenge scripts |
| Pilot | 1 week | Internal testing, feedback incorporation |
| Launch | - | Public availability |

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Engineering Lead | | | |
| Solutions Architect | | | |
| Workshop Lead | | | |
