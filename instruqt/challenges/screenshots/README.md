# Screenshot Placeholders

This directory should contain screenshots for the workshop challenges. Each screenshot helps participants understand what they should see at each step.

## Required Screenshots

### Challenge 01 - Setup and Baseline

| Filename | Description |
|----------|-------------|
| `01-apm-services-list.png` | APM Services view showing order-service, inventory-service, payment-service with healthy status indicators and baseline metrics (latency ~100-300ms, low error rate) |
| `01-service-map.png` | Service Map showing order-service in center with arrows to inventory-service and payment-service |
| `01-slo-dashboard-healthy.png` | SLO dashboard with both SLOs showing green status, high SLI percentages (99%+), minimal error budget consumption |
| `01-healthy-trace-waterfall.png` | Trace waterfall for a normal request (~100-300ms total), showing order-service parent span with child spans for inventory and payment calls |

### Challenge 02 - Deploy and Detect

| Filename | Description |
|----------|-------------|
| `02-latency-spike.png` | APM latency chart showing dramatic spike from ~200ms to ~2000ms with deployment annotation line marking when v1.1-bad was deployed |
| `02-slo-degradation.png` | SLO dashboard showing Latency SLO in yellow/red state, elevated burn rate (6x+), error budget being consumed |
| `02-alert-fired.png` | Alerts page showing "SLO Burn Rate" alert in Active/Firing state with alert details panel |

### Challenge 03 - Investigate and Remediate

| Filename | Description |
|----------|-------------|
| `03-apm-correlations.png` | Correlations panel highlighting service.version=v1.1-bad with high impact percentage |
| `03-smoking-gun-span.png` | Trace waterfall (~2100ms total) with "detailed-trace-logging" span dominating the timeline (~2000ms) |
| `03-span-attributes.png` | Span detail panel showing custom attributes: logging.author, logging.commit_sha, logging.pr_number, logging.delay_ms |
| `03-log-correlation.png` | Logs view filtered by trace.id showing correlated log message with timestamp, service name, and debug message about 2000ms delay |
| `03-recovery-latency.png` | APM latency chart showing full incident lifecycle: baseline → spike → return to baseline (mountain shape) |

### Challenge 04 - Learn and Prevent

| Filename | Description |
|----------|-------------|
| `04-agent-builder-interface.png` | AI Assistants page showing "NovaMart Incident Investigation Assistant" agent card |
| `04-agent-conversation.png` | Conversation with agent showing incident timeline response with tools used visible |
| `04-case-created.png` | Completed Case with title, description, tags, and linked alert |

## Screenshot Guidelines

1. **Resolution:** Capture at 1920x1080 or higher
2. **Format:** PNG preferred for clarity
3. **Annotations:** Consider adding red boxes/arrows to highlight key areas
4. **Sensitive Data:** Blur or redact any real API keys, endpoints, or personal information
5. **Consistency:** Use the same Kibana theme (light/dark) across all screenshots
6. **Timing:** Capture during active workshop run with realistic data

## How to Capture

1. Run through the workshop completely
2. At each screenshot point, pause and capture
3. For "before/after" shots (like latency spike), you may need to time it carefully
4. Use browser dev tools to capture full page if needed

## Alternative: Animated GIFs

For complex interactions (like watching the latency spike in real-time), consider short animated GIFs instead of static screenshots.
