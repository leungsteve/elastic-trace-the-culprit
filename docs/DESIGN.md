# Design Document

## From Commit to Culprit: An Elastic Observability Workshop

**Version:** 1.0  
**Last Updated:** December 2024  
**Author:** Solutions Architecture Team

---

## Overview

This document describes the design of the "From Commit to Culprit" workshop, including user experience flows, interface designs, and narrative structure.

---

## Design Principles

1. **Story-driven learning:** Every technical concept is introduced through the narrative
2. **Progressive disclosure:** Complexity increases gradually across challenges
3. **Hands-on first:** Participants do, then understand why
4. **Real-world relevance:** Scenarios mirror actual production incidents
5. **Celebration of discovery:** Each "aha moment" is designed and anticipated

---

## Narrative Design

### Setting

**Company:** NovaMart  
**Industry:** E-commerce  
**Tagline:** "Shop smarter, ship faster"

NovaMart is a mid-size e-commerce company experiencing rapid growth. Their microservices architecture was built quickly to meet demand, and they are now focused on improving reliability and observability.

### Characters

#### Alex Chen (Protagonist)
- **Role:** On-call SRE
- **Personality:** Methodical, calm under pressure, loves data
- **Workshop function:** The participant's avatar. Instructions are framed as "You are Alex..."

#### Jordan Rivera (Catalyst)
- **Role:** Order Service Tech Lead
- **Personality:** Well-intentioned but overconfident, ships fast
- **Workshop function:** The developer who deployed the bad code. Referenced but never blamed harshly.

#### Sam Patel (Mentor)
- **Role:** Platform Engineering Manager
- **Personality:** Pragmatic, focused on MTTR and reliability
- **Workshop function:** Provides context and business perspective.

### Story Arc

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NARRATIVE ARC                                         │
│                                                                                 │
│  EXPOSITION          RISING ACTION       CLIMAX           RESOLUTION           │
│  ───────────         ──────────────      ──────           ──────────           │
│                                                                                 │
│  "Normal Friday"     "Something's        "Found it!"      "Lessons learned"    │
│                       wrong"                                                    │
│       │                    │                  │                  │              │
│       ▼                    ▼                  ▼                  ▼              │
│  ┌─────────┐         ┌─────────┐        ┌─────────┐        ┌─────────┐         │
│  │Challenge│         │Challenge│        │Challenge│        │Challenge│         │
│  │    1    │────────►│    2    │───────►│    3    │───────►│    4    │         │
│  │         │         │         │        │         │        │         │         │
│  │ Setup & │         │ Deploy &│        │Investig.│        │ Learn & │         │
│  │Baseline │         │ Detect  │        │& Remed. │        │ Prevent │         │
│  └─────────┘         └─────────┘        └─────────┘        └─────────┘         │
│                                                                                 │
│  Emotional    Calm ──► Tension ──► Urgency ──► Relief ──► Satisfaction         │
│  Journey                                                                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Challenge Design

### Challenge 1: Setup and Baseline

**Duration:** 20 minutes

**Opening Narrative:**
> *It is Friday afternoon at NovaMart headquarters. You are Alex Chen, the on-call SRE for the weekend. Before heading into the weekend, you want to make sure everything looks healthy. Sam Patel, your manager, always says: "You cannot detect anomalies if you do not know what normal looks like."*

**Learning Objectives:**
- Verify environment connectivity
- Navigate Kibana's Observability UI
- Understand SLO concepts and error budgets
- Establish mental model of "healthy" state

**Key Activities:**

| Activity | Duration | Kibana Location |
|----------|----------|-----------------|
| Verify services in APM | 3 min | Observability > APM > Services |
| Explore service map | 3 min | Observability > APM > Service Map |
| Review SLO dashboard | 5 min | Observability > SLOs |
| Understand error budget | 3 min | SLO detail view |
| Generate baseline traffic | 3 min | Terminal |
| Explore a healthy trace | 3 min | Observability > APM > Traces |

**Success Criteria:**
- All three services visible in APM
- SLOs showing healthy (green) status
- Participant can navigate between APM, Logs, Metrics
- Baseline traffic generating visible traces

**Checkpoint Question:**
> "What is the current SLI for the Order Service latency SLO?"

---

### Challenge 2: Deploy and Detect

**Duration:** 30 minutes

**Opening Narrative:**
> *At 2:47 PM, Jordan Rivera from the Order Service team sends a message to the #deployments channel: "Just shipped v1.1 with some performance optimizations. QA signed off. Happy Friday everyone!" You note the deployment and continue your work. Five minutes later, your phone buzzes. An alert has fired. Your weekend plans are about to change.*

**Learning Objectives:**
- Execute a deployment using the simulation script
- Observe real-time impact on SLOs and metrics
- Understand alert triggering mechanisms
- Visualize business impact

**Key Activities:**

| Activity | Duration | Location |
|----------|----------|----------|
| Review deployment command | 2 min | Terminal |
| Execute deployment | 3 min | Terminal |
| Observe latency increase | 5 min | Observability > APM > Services |
| Watch SLO burn rate | 5 min | Observability > SLOs |
| See alert fire | 3 min | Observability > Alerts |
| View business impact | 5 min | Dashboard |
| Observe deployment annotation | 3 min | APM timeline |
| Discuss detection layers | 4 min | Facilitator-led |

**Deployment Command:**
```bash
./deploy.sh order-service v1.1-bad
```

**Expected Output:**
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

**Observation Points:**

1. **APM Service Overview:** Watch latency chart climb
2. **SLO Dashboard:** See burn rate turn red
3. **Business Impact:** Watch revenue counter tick up
4. **Alerts:** See SLO burn rate alert fire

**Checkpoint Question:**
> "What is the current burn rate for the Order Latency SLO?"

---

### Challenge 3: Investigate and Remediate

**Duration:** 25 minutes

**Opening Narrative:**
> *The alert is clear: Order Service latency has spiked. Customers are complaining on social media. Sam Patel pings you: "Alex, what is happening? Can you get this resolved before the weekend rush?" You take a deep breath. Time to find the culprit.*

**Learning Objectives:**
- Navigate from alert to root cause
- Use APM Correlations to identify issues
- Correlate traces with logs
- Understand automated remediation
- Verify system recovery

**Key Activities:**

| Activity | Duration | Location |
|----------|----------|----------|
| Drill down from alert | 3 min | Alerts > APM |
| Use APM Correlations | 4 min | APM > Correlations |
| Examine slow trace | 5 min | APM > Traces > Detail |
| View span attributes | 3 min | Span detail panel |
| Correlate with logs | 4 min | Logs UI (filtered) |
| Observe automated rollback | 3 min | Terminal + APM |
| Verify recovery | 3 min | SLOs + APM |

**Investigation Journey:**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    INVESTIGATION FLOW                                           │
│                                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐       │
│  │  ALERT  │───►│ SERVICE │───►│ TRACE   │───►│  SPAN   │───►│  LOGS   │       │
│  │         │    │   MAP   │    │WATERFALL│    │ DETAILS │    │         │       │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘       │
│       │              │              │              │              │             │
│       ▼              ▼              ▼              ▼              ▼             │
│  "SLO burn     "Order svc    "2-second      "Author:        "delay:           │
│   rate high"   is red"       span found"    jordan"         2000ms"           │
│                                                                                 │
│  APM CORRELATIONS ─────────────────────────────────────────────────────────►   │
│  "service.version: v1.1-bad has 94% correlation with high latency"              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key Discovery Moments:**

1. **APM Correlations shows:** `service.version: v1.1-bad` is 94% correlated with slow requests
2. **Trace waterfall shows:** `detailed-trace-logging` span taking 2,001ms
3. **Span attributes show:** `logging.author: jordan.rivera`, `logging.commit_sha: a1b2c3d4`, `logging.destination: /var/log/orders/trace.log`
4. **Logs show:** "Writing detailed trace data to disk: 2000ms" at OrderController.java:47

**Rollback Observation:**
> *While you are investigating, you notice the Order Service container restarting. The Workflow has automatically triggered a rollback. Within minutes, the SLO burn rate returns to normal.*

**Checkpoint Question:**
> "What was the name of the span that caused the latency spike?"

#### Timing Notes

- If the alert has not fired after 5 minutes, participants can check Stack Management > Rules to verify rule status
- A `manual-trigger.sh` script can force the alert condition for demos
- If participants are running behind, facilitators can use the fast-forward option: "If you are running behind, ask your facilitator for the fast-forward option"

---

### Challenge 4: Learn and Prevent

**Duration:** 15 minutes

**Opening Narrative:**
> *The rollback is complete. Latency is back to normal. Jordan Rivera messages you privately: "Hey Alex, sorry about that. I thought I had tested everything. Can you help me understand what went wrong?" You smile. This is the part of the job you actually enjoy: turning incidents into lessons.*

**Learning Objectives:**
- Use Agent Builder for conversational analysis
- Create a Case for incident documentation
- Calculate total business impact
- Understand prevention strategies

**Key Activities:**

| Activity | Duration | Location |
|----------|----------|----------|
| Open Agent Builder | 2 min | Kibana > Agents |
| Ask about incident timeline | 3 min | Agent Chat |
| Request code diff | 3 min | Agent Chat |
| Calculate business impact | 2 min | Agent Chat |
| Create Case from alert | 3 min | Alerts > Create Case |
| Wrap-up discussion | 2 min | Facilitator-led |

**Agent Builder Conversations:**

**Example 1: Incident Timeline**
> **Participant:** "What happened in the last hour?"
>
> **Agent:** "Here is the incident timeline:
> - 14:45:00 - Deployment: order-service v1.1-bad (commit a1b2c3d4, author: jordan.rivera)
> - 14:47:23 - First slow transaction detected (2,347ms)
> - 14:49:00 - SLO burn rate exceeded 6x threshold
> - 14:49:15 - SLO Burn Rate alert fired
> - 14:49:18 - Automated rollback triggered
> - 14:51:00 - Service recovered to v1.0
> - 14:53:00 - Alert resolved"

**Example 2: Code Changes**
> **Participant:** "What code changed between v1.0 and v1.1?"
>
> **Agent:** "The deployment v1.1-bad (commit a1b2c3d4) by Jordan Rivera included the following change in OrderController.java:
> ```diff
> + // Performance optimization for connection pooling
> + Thread.sleep(2000);
> ```
> This added a 2-second sleep to every order request, causing the latency spike."

**Example 3: Business Impact**
> **Participant:** "What was the total business impact?"
>
> **Agent:** "During the 6-minute incident window, the Order Service experienced a 12.3% error rate across 487 transactions. This resulted in 60 failed orders with an estimated revenue impact of $2,850. Additionally, the SLO burned through 8% of the monthly error budget."

**Case Creation:**
Participants create a Case with:
- Title: "Order Service Latency Incident - 2024-01-15"
- Description: Summary of findings
- Attachments: Alert, relevant traces
- Assignee: Jordan Rivera (for follow-up)

---

## UI Navigation Paths

### Path 1: Alert to Root Cause

```
Observability > Alerts
    └─► Click alert "Order Service SLO Burn Rate"
        └─► Click "View in APM"
            └─► Click "Correlations" tab
                └─► Note: service.version: v1.1-bad (94% impact)
                    └─► Click "View transactions"
                        └─► Click slow transaction
                            └─► Expand "connection-pool-optimization" span
                                └─► View span attributes (author, commit)
```

### Path 2: Trace to Logs

```
Observability > APM > Traces
    └─► Select slow trace
        └─► Copy trace.id from metadata
            └─► Navigate to Logs
                └─► Add filter: trace.id: <copied-id>
                    └─► View correlated log messages
```

### Path 3: SLO to Impact

```
Observability > SLOs
    └─► Click "Order Service Latency"
        └─► View burn rate chart
            └─► Click "Error budget" tab
                └─► Navigate to Dashboard
                    └─► View business impact panel
```

---

## Visual Design

### Color Palette (Elastic Brand)

| Color | Hex | Usage |
|-------|-----|-------|
| Elastic Teal | #00BFB3 | Success, healthy state |
| Elastic Pink | #F04E98 | Alerts, errors |
| Elastic Blue | #1BA9F5 | Links, interactive elements |
| Dark Gray | #343741 | Text |
| Light Gray | #F5F7FA | Backgrounds |

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     NOVAMART ORDER SERVICE DASHBOARD                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │   ORDERS/HOUR   │  │  AVG ORDER $    │  │  ERROR RATE     │                 │
│  │      487        │  │     $47.50      │  │     12.3%       │                 │
│  │   ▼ 23% vs avg  │  │                 │  │   ▲ from 0.5%   │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                           │ │
│  │   💰 ESTIMATED REVENUE IMPACT                                             │ │
│  │                                                                           │ │
│  │              $2,847 / hour                                                │ │
│  │              in failed orders                                             │ │
│  │                                                                           │ │
│  │   Since incident started (47 min):  $2,230 total                          │ │
│  │                                                                           │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────────┐ │
│  │   SLO STATUS                    │  │   ERROR BUDGET                      │ │
│  │   ████████░░ 78.2%              │  │   ████░░░░░░ 43% remaining          │ │
│  │   Order Latency SLO             │  │   Burning 5.2x sustainable rate     │ │
│  └─────────────────────────────────┘  └─────────────────────────────────────┘ │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │   LATENCY OVER TIME                                                       │ │
│  │                                                                           │ │
│  │   ms │              ▲ Deployed v1.1-bad                                   │ │
│  │  2500│              │ ╭─────────────────                                  │ │
│  │  2000│              │╱                                                    │ │
│  │  1500│              │                                                     │ │
│  │  1000│──────────────│                                                     │ │
│  │   500│              │                                                     │ │
│  │      └──────────────┴──────────────────────────────────────────────►     │ │
│  │                  14:47                                        Time        │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Error Handling

### Common Issues and Resolutions

| Issue | Detection | Resolution Message |
|-------|-----------|-------------------|
| Services not starting | Health check fails | "Run `docker-compose logs <service>` to see error details" |
| No traces in APM | APM shows 0 services | "Verify ELASTIC_ENDPOINT and ELASTIC_API_KEY in .env" |
| Alert not firing | No alert after 5 min | "Check alert rule status in Stack Management > Rules" |
| Workflow not triggering | No rollback after alert | "Verify webhook URL is accessible from Elastic Cloud" |
| Agent Builder unavailable | 404 on Agents page | "Agent Builder requires Elastic Cloud Serverless" |

---

## Accessibility Considerations

1. **Keyboard navigation:** All Kibana interactions are keyboard-accessible
2. **Screen reader support:** Challenge instructions use semantic headings
3. **Color independence:** Status is conveyed by icons in addition to color
4. **Copy-paste commands:** All commands are provided in code blocks for easy copying

---

## Facilitator Notes

### Timing Adjustments

- If participants are moving quickly, encourage exploration of additional APM features
- If participants are falling behind, use "solve" scripts to catch up
- Build in 10-minute buffer for Q&A and troubleshooting

### Common Questions

| Question | Answer |
|----------|--------|
| "Would this work in production?" | "Yes, but you would configure longer SLO windows and more sophisticated rollback logic" |
| "How long does ML baselining take?" | "Hours to days depending on data volume. We pre-trained for this workshop." |
| "Can we trigger multiple alerts?" | "Yes, threshold alert may also fire. They complement each other." |

### Engagement Tips

1. Ask participants to predict what will happen before each step
2. Celebrate discoveries ("Who found the span attributes first?")
3. Connect concepts to participants' own environments
4. Encourage screenshots for later reference
