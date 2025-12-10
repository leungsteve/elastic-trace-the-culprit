# Characters and Narrative Guide

## From Commit to Culprit: An Elastic Observability Workshop

**Version:** 1.0  
**Last Updated:** December 2024  
**Author:** Solutions Architecture Team

---

## Overview

This document provides detailed character profiles and narrative guidelines to create an engaging, story-driven workshop experience. The characters and company setting provide context that makes technical concepts memorable and relatable.

---

## Company Profile

### NovaMart

**Industry:** E-commerce  
**Size:** Mid-market (500 employees)  
**Founded:** 2018  
**Headquarters:** Austin, Texas  
**Tagline:** "Shop smarter, ship faster"

**Company Background:**
NovaMart started as a niche electronics retailer and grew rapidly during the pandemic shift to online shopping. The engineering team expanded quickly, adopting microservices to scale. They are now focused on reliability and observability as customer expectations increase.

**Business Metrics:**
- Average order value: $47.50
- Daily orders: ~15,000
- Peak orders per hour: 2,500 (during flash sales)
- Uptime target: 99.9%

**Technology Stack:**
- Microservices architecture (12 services total)
- Kubernetes in production
- Elastic Observability for monitoring
- GitHub for source control
- Jenkins for CI/CD

**Engineering Culture:**
- Ship fast, but measure everything
- Blameless post-mortems
- On-call rotation shared across teams
- Strong documentation culture

---

## Main Characters

### Alex Chen (Protagonist)

**Role:** Site Reliability Engineer  
**Team:** Platform Engineering  
**Reports to:** Sam Patel  
**Tenure:** 2 years at NovaMart

**Background:**
Alex joined NovaMart from a traditional ops role at a larger company. They were initially skeptical of the "you build it, you run it" culture but have come to appreciate the ownership model. Alex is methodical, calm under pressure, and takes pride in building reliable systems.

**Personality Traits:**
- Methodical: Follows runbooks but knows when to improvise
- Curious: Always wants to understand why, not just what
- Empathetic: Remembers that developers are trying their best
- Humble: Quick to admit when they do not know something

**Technical Skills:**
- Expert in Kubernetes and container orchestration
- Proficient with Elastic Observability
- Comfortable with Java, Python, and Go
- Strong understanding of distributed systems

**Communication Style:**
- Prefers Slack for async, Zoom for incidents
- Documents everything in Confluence
- Asks clarifying questions before acting
- Uses data to support arguments

**Workshop Role:**
Alex is the participant's avatar. Challenge instructions are written from Alex's perspective, and decisions are framed as "What would Alex do?"

**Sample Dialogue:**
> "Let me check the traces first. I want to understand the full request path before jumping to conclusions."

> "The SLO is burning fast, but let us not panic. The automation should kick in any second now."

> "Jordan's code looks fine at first glance, but the proof is in the telemetry."

---

### Jordan Rivera (Catalyst)

**Role:** Senior Software Engineer, Tech Lead  
**Team:** Order Service  
**Reports to:** Engineering Manager  
**Tenure:** 3 years at NovaMart

**Background:**
Jordan was one of the early engineers at NovaMart and helped build the Order Service from scratch. They are passionate about performance and are always looking for ways to make the system faster. Sometimes this enthusiasm leads to shortcuts.

**Personality Traits:**
- Enthusiastic: Loves shipping new features
- Confident: Sometimes overconfident in their code
- Collaborative: Quick to pair and help others
- Growth-minded: Takes feedback well after initial defensiveness

**Technical Skills:**
- Expert in Java and Spring Boot
- Deep knowledge of the Order Service codebase
- Good understanding of database optimization
- Learning more about observability (motivated by this incident)

**Communication Style:**
- Active in #deployments Slack channel
- Announces changes proactively
- Sometimes skips PR review for "small" changes
- Writes detailed commit messages

**Workshop Role:**
Jordan is the developer who deploys the bad code. They are not a villain. They had good intentions (improving performance) but made a mistake. The narrative should be sympathetic.

**Sample Dialogue:**
> "Just shipped v1.1 with some detailed trace logging for debugging. QA signed off. Happy Friday everyone! 🚀"

> "Wait, what? The latency is... oh no. I thought I disabled the synchronous file writes."

> "Alex, I am so sorry. Can you walk me through how you found it? I want to learn from this."

**The Bad Code Context:**
Jordan was working on improving observability for the Order Service. They enabled detailed trace logging that writes verbose trace data to disk for debugging purposes. The logging uses synchronous file I/O, which adds a 2-second delay to every request. Jordan tested it in staging where disk I/O was fast, but forgot to disable it before deploying to production. The code review was rushed on a Friday afternoon, and the reviewer did not notice the synchronous write pattern.

---

### Sam Patel (Mentor)

**Role:** Platform Engineering Manager  
**Team:** Platform Engineering  
**Reports to:** VP of Engineering  
**Tenure:** 4 years at NovaMart

**Background:**
Sam built the Platform Engineering team from the ground up. They have seen NovaMart grow from a monolith to microservices and have learned (sometimes painfully) what it takes to run reliable systems at scale. Sam believes in automation and blameless culture.

**Personality Traits:**
- Strategic: Thinks about long-term reliability
- Supportive: Advocates for the team
- Pragmatic: Balances ideal with achievable
- Communicative: Keeps stakeholders informed

**Communication Style:**
- Prefers high-level summaries
- Asks about business impact first
- Encourages documentation and post-mortems
- Shields team from unnecessary escalations

**Workshop Role:**
Sam provides context and business perspective. They appear in narrative moments to frame why things matter (e.g., "Every minute of degradation costs us money").

**Sample Dialogue:**
> "Alex, what is happening with Order Service? I am getting pings from the VP. Can you give me a quick status?"

> "Good work on that investigation. Let us make sure we capture this in a post-mortem so everyone learns."

> "The automation worked exactly as designed. This is why we invested in SLOs and Workflows."

---

### The Elastic AI Agent (Assistant)

**Role:** AI-powered investigation assistant  
**Location:** Agent Builder in Kibana

**Personality:**
- Helpful and concise
- Proactive with relevant information
- Never judgmental about the incident
- Suggests next steps

**Capabilities:**
- Query telemetry data conversationally
- Calculate business impact
- Generate incident timelines
- Retrieve code change information

**Sample Interactions:**

**User:** "What happened in the last hour?"

**Agent:** "Here is the incident timeline:
- 14:45:00: Deployment of order-service v1.1-bad (commit a1b2c3d4 by jordan.rivera)
- 14:47:23: First transaction exceeded 2-second threshold
- 14:49:00: SLO burn rate exceeded 6x sustainable rate
- 14:49:15: SLO Burn Rate alert fired
- 14:49:18: Automated rollback initiated via Workflow
- 14:51:00: Service recovered to v1.0
- 14:53:00: Alert resolved

Would you like me to calculate the business impact during this window?"

---

## Supporting Cast

### Maya Wong
**Role:** QA Engineer  
**Relevance:** Signed off on v1.1 (missed the bug because test environment did not have realistic load)

### Derek Johnson
**Role:** VP of Engineering  
**Relevance:** Gets pings during major incidents, Sam shields the team from escalation

### Customer Support Bot (mentioned in narrative)
**Relevance:** Starts receiving complaints about slow checkout, adding urgency

---

## Narrative Structure

### Act 1: The Setup (Challenge 1)

**Tone:** Calm, educational  
**Purpose:** Establish baseline, introduce tools

**Opening:**
> *It is Friday afternoon at NovaMart headquarters. The week has been uneventful. Order volumes are steady. No pages overnight. You are Alex Chen, the on-call SRE for the weekend shift.*
>
> *Before heading into the weekend, you want to make sure everything looks healthy. Sam Patel, your manager, always says: "You cannot detect anomalies if you do not know what normal looks like."*

**Character Moments:**
- Alex reviewing dashboards methodically
- Sam's wisdom about baselines
- Healthy system as a character (everything green)

### Act 2: The Incident (Challenges 2-3)

**Tone:** Urgent but controlled  
**Purpose:** Create tension, demonstrate investigation

**Inciting Incident:**
> *At 2:47 PM, a message appears in #deployments:*
>
> **jordan.rivera:** Just shipped v1.1 with some performance optimizations. QA signed off. Happy Friday everyone! 🚀
>
> *You note the deployment and continue your work. Five minutes later, your phone buzzes. An alert has fired. Your weekend plans are about to change.*

**Rising Action:**
- Alert fires, urgency increases
- Business impact visible (money counter)
- Investigation reveals the smoking gun
- Automated rollback provides relief

**Character Moments:**
- Alex staying calm under pressure
- Jordan's optimistic deployment message (dramatic irony)
- Sam asking for status updates
- The relief of automated remediation

### Act 3: The Resolution (Challenge 4)

**Tone:** Reflective, forward-looking  
**Purpose:** Consolidate learning, establish practices

**Resolution:**
> *The rollback is complete. Latency is back to normal. Your phone stops buzzing. Jordan Rivera sends you a private message:*
>
> **jordan.rivera:** Hey Alex, sorry about that. I thought I had tested everything. Can you help me understand what went wrong?
>
> *You smile. This is the part of the job you actually enjoy: turning incidents into lessons.*

**Character Moments:**
- Jordan seeking to learn (not defensive)
- Alex as teacher and mentor
- Sam praising the team's response
- Agent Builder as helpful assistant

---

## Dialogue Guidelines

### Do:
- Use natural, conversational language
- Include technical details that feel realistic
- Show characters being human (making mistakes, learning)
- Use Slack-style formatting for messages

### Do Not:
- Make anyone a villain
- Use overly formal language
- Include unnecessary drama
- Break the fourth wall (avoid "in this workshop...")

### Sample Slack Messages

**#deployments channel:**
```
jordan.rivera  2:47 PM
Just shipped v1.1 with some detailed trace logging for debugging. QA signed off. Happy Friday everyone! 🚀

maya.wong  2:48 PM
Nice! What did you add?

jordan.rivera  2:48 PM
Verbose trace logs to disk. Should help us debug those intermittent order failures. Tested great in staging.

sam.patel  2:49 PM
👍 Thanks for the heads up Jordan
```

**#incidents channel (later):**
```
alert-bot  2:52 PM
🚨 ALERT: Order Service SLO Burn Rate
Severity: High
Service: order-service
Burn Rate: 6.2x sustainable

alex.chen  2:53 PM
On it. Looking at traces now.

sam.patel  2:54 PM
@alex.chen what is the blast radius? Getting pings from Derek.

alex.chen  2:55 PM
Order latency is up. Investigating the recent deployment. Automation should trigger any second.

alex.chen  2:56 PM
Update: Automated rollback triggered. Watching for recovery.

alex.chen  2:59 PM
✅ Service recovered. Latency back to normal. Will post RCA shortly.

jordan.rivera  3:00 PM
Oh no. Was this my deployment? 😰

alex.chen  3:01 PM
Looks like it, but no worries. Let us sync after I document the timeline. The automation caught it fast.
```

---

## Tone Guidelines by Challenge

| Challenge | Primary Tone | Secondary Tone | Emotion |
|-----------|--------------|----------------|---------|
| 1: Setup | Educational | Calm | Confidence |
| 2: Deploy | Urgent | Controlled | Tension |
| 3: Investigate | Detective | Methodical | Discovery |
| 4: Learn | Reflective | Collaborative | Satisfaction |

---

## Character Voice Quick Reference

| Character | One-liner Style | Emoji Use | Technical Depth |
|-----------|-----------------|-----------|-----------------|
| Alex | "Let me check the data first." | Minimal | High |
| Jordan | "Shipped it! Should be faster now." | Frequent | Medium |
| Sam | "What is the business impact?" | None | Low (strategic) |
| Agent | "Based on the telemetry, here is what I found." | None | High |

---

## Cultural Considerations

The workshop should feel:
- **Inclusive:** Characters have diverse names and backgrounds
- **Blameless:** Mistakes happen; learning is emphasized
- **Realistic:** Technical details ring true for practitioners
- **Positive:** Even incidents are opportunities for growth

Avoid:
- Gendered assumptions about roles
- Stereotypes about engineers or ops
- Blame or finger-pointing
- Overly dramatic conflict
