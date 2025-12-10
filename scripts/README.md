# Workshop Scripts

This directory contains all operational scripts for the "From Commit to Culprit" workshop.

## Quick Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `build-images.sh` | Build all Docker images | `./build-images.sh` |
| `deploy.sh` | Deploy a service version | `./deploy.sh order-service v1.1-bad` |
| `rollback.sh` | Rollback to v1.0 | `./rollback.sh order-service` |
| `health-check.sh` | Check all services | `./health-check.sh` |
| `load-generator.sh` | Generate traffic | `./load-generator.sh --rate 3` |
| `workshop-test.sh` | **Test full workshop flow** | `./workshop-test.sh --manual-rollback` |
| `setup-elastic.sh` | Provision Elastic assets | `./setup-elastic.sh` |
| `generate-baseline.sh` | Generate baseline data | `./generate-baseline.sh` |
| `auto-rollback-monitor.sh` | Monitor for auto-rollback | `./auto-rollback-monitor.sh` |

## Workshop Testing

### Quick Test

Test the complete workshop flow in 4-5 minutes:

```bash
./workshop-test.sh --manual-rollback
```

This will:
1. ✓ Verify all services are healthy
2. ✓ Check baseline latency (<500ms)
3. ✓ Deploy v1.1-bad
4. ✓ Verify latency degrades (>1500ms)
5. ✓ Trigger rollback
6. ✓ Verify recovery

**For detailed documentation, see:** [docs/WORKSHOP-TEST-GUIDE.md](../docs/WORKSHOP-TEST-GUIDE.md)

### Test Options

```bash
# Full test with automated rollback (requires webhook setup)
./workshop-test.sh

# Manual rollback mode (recommended for initial testing)
./workshop-test.sh --manual-rollback

# Skip baseline check (faster for repeated testing)
./workshop-test.sh --skip-baseline --manual-rollback

# Get help
./workshop-test.sh --help
```

## Pre-Workshop Checklist

Before running a workshop, execute these scripts in order:

```bash
# 1. Build all images
./build-images.sh

# 2. Start services (from infra directory)
cd ../infra
docker-compose up -d
cd ../scripts

# 3. Check health
./health-check.sh

# 4. Test workshop flow
./workshop-test.sh --manual-rollback

# 5. If all tests pass, you're ready!
```

## Script Details

### build-images.sh

Builds Docker images for all services and pushes to local registry.

**Requirements:**
- Docker running
- Local registry running (port 5000)

**Output:**
- `localhost:5000/order-service:v1.0`
- `localhost:5000/order-service:v1.1-bad`
- `localhost:5000/inventory-service:v1.0`
- `localhost:5000/payment-service:v1.0`
- `localhost:5000/rollback-webhook:v1.0`

### deploy.sh

Simulates a CI/CD deployment by:
1. Updating .env with new version
2. Pulling image from registry
3. Restarting service with docker-compose
4. Sending deployment annotation to Elastic APM
5. Health checking the service

**Example:**
```bash
./deploy.sh order-service v1.1-bad
```

**Valid services:**
- `order-service`
- `inventory-service`
- `payment-service`

**Valid versions:**
- `v1.0` (good version)
- `v1.1-bad` (introduces 2-second sleep bug)

### rollback.sh

Convenience wrapper around deploy.sh that always deploys v1.0.

**Example:**
```bash
./rollback.sh order-service
```

Equivalent to:
```bash
./deploy.sh order-service v1.0
```

### health-check.sh

Comprehensive health check for all workshop components:
- Order Service
- Inventory Service
- Payment Service
- Rollback Webhook
- OTEL Collector
- Docker daemon
- Elastic Cloud connection
- Container registry

**Example:**
```bash
./health-check.sh
```

**Exit codes:**
- `0` - All healthy
- `1` - Some services unhealthy

### load-generator.sh

Generates realistic traffic to the Order Service.

**Basic usage:**
```bash
# Run forever at 3 requests/second
./load-generator.sh

# Run for 5 minutes
./load-generator.sh --duration 300

# Run at 5 requests/second for 2 minutes
./load-generator.sh --rate 5 --duration 120

# Stop with Ctrl+C
```

**Features:**
- Random product selection
- Random quantities
- Jitter to simulate real traffic patterns
- Real-time success/failure reporting
- Statistics summary on exit

### workshop-test.sh

**NEW!** Automated end-to-end test of the complete workshop flow.

See [docs/WORKSHOP-TEST-GUIDE.md](../docs/WORKSHOP-TEST-GUIDE.md) for complete documentation.

**Quick start:**
```bash
./workshop-test.sh --manual-rollback
```

### setup-elastic.sh

Provisions Elastic Cloud with all workshop assets:
- ML anomaly detection jobs
- SLOs (latency and availability)
- Alert rules (threshold and burn rate)
- Webhook connector
- Workflow actions
- Agent Builder tools (7 tools)
- Agent Builder agent
- Dashboards
- Deployment metadata

**Requirements:**
- `ELASTIC_ENDPOINT` in .env
- `ELASTIC_API_KEY` in .env
- `KIBANA_URL` in .env

**Example:**
```bash
./setup-elastic.sh
```

### generate-baseline.sh

Generates synthetic baseline data for ML model training.

**Example:**
```bash
./generate-baseline.sh --duration 3600  # 1 hour of data
```

### auto-rollback-monitor.sh

Monitors for automated rollback events and logs them.

**Example:**
```bash
./auto-rollback-monitor.sh
```

**Useful for:**
- Testing automated rollback workflow
- Debugging webhook calls
- Timing measurements

## Testing Workflow

### Initial Setup Test

```bash
# Start fresh
cd ../infra
docker-compose down -v

# Build everything
cd ../scripts
./build-images.sh

# Start services
cd ../infra
docker-compose up -d

# Wait for healthy state
cd ../scripts
./health-check.sh

# Run complete test
./workshop-test.sh --manual-rollback
```

### Daily Smoke Test

```bash
# Quick health check
./health-check.sh

# If healthy, test deployment/rollback cycle
./workshop-test.sh --skip-baseline --manual-rollback
```

### Pre-Workshop Validation

```bash
# Full test including baseline
./workshop-test.sh --manual-rollback

# Manual Kibana verification
# - Open Kibana
# - Navigate through each challenge
# - Verify all UI elements present
# - Test Agent Builder queries

# Test automated rollback (if configured)
./workshop-test.sh  # without --manual-rollback
```

## Common Issues

### "Permission denied" when running scripts

```bash
# Make scripts executable
chmod +x *.sh
```

### "docker-compose: command not found"

```bash
# Install Docker Compose or use docker compose (v2)
# In scripts, replace docker-compose with docker compose
```

### "Connection refused" for services

```bash
# Check containers are running
docker-compose -f ../infra/docker-compose.yml ps

# Check logs
docker-compose -f ../infra/docker-compose.yml logs <service-name>

# Restart services
docker-compose -f ../infra/docker-compose.yml restart
```

### Tests fail with high latency

```bash
# Check system load
top

# Check Docker resources
docker stats

# Increase thresholds in workshop-test.sh if needed
```

### Automated rollback doesn't trigger

This is expected without proper webhook setup. Use `--manual-rollback` flag:

```bash
./workshop-test.sh --manual-rollback
```

For automated rollback, you need:
1. Public webhook URL (use ngrok locally)
2. Webhook connector in Kibana
3. SLO burn rate alert rule
4. Workflow action configured

See [docs/WORKSHOP-TEST-GUIDE.md](../docs/WORKSHOP-TEST-GUIDE.md) for setup instructions.

## Script Dependencies

```
build-images.sh
    └─> Requires: Docker, local registry

deploy.sh
    ├─> Requires: ../infra/.env, docker-compose.yml
    └─> Calls: curl (for deployment annotation)

rollback.sh
    └─> Calls: deploy.sh

health-check.sh
    ├─> Requires: curl
    └─> Reads: ../infra/.env

load-generator.sh
    └─> Requires: curl, bc

workshop-test.sh
    ├─> Calls: deploy.sh, rollback.sh
    ├─> Requires: curl, bc
    └─> Reads: ../infra/.env

setup-elastic.sh
    ├─> Requires: curl, jq
    └─> Reads: ../infra/.env, ../elastic-assets/*

generate-baseline.sh
    └─> Calls: load-generator.sh

auto-rollback-monitor.sh
    └─> Requires: docker, grep
```

## Exit Codes

All scripts follow this convention:
- `0` - Success
- `1` - Failure/Error

This makes them CI/CD friendly.

## Logging

Scripts use colored output:
- 🟢 **Green** `[PASS]` - Success
- 🔴 **Red** `[FAIL]` - Failure
- 🟡 **Yellow** `[WARN]` - Warning
- 🔵 **Blue** `[INFO]` - Information
- 🔵 **Blue** `[STEP]` - Process step
- 🟡 **Yellow** `[TEST]` - Test case

## Contributing

When adding new scripts:

1. **Follow naming convention:** `verb-noun.sh` (e.g., `check-health.sh`)
2. **Include header comment block** with description and usage
3. **Use consistent styling:** Reference existing scripts
4. **Add to this README:** Document purpose, usage, examples
5. **Add to .gitignore if needed:** For scripts that generate local files
6. **Make executable:** `chmod +x new-script.sh`
7. **Test thoroughly:** Run in clean environment

## Support

For issues or questions:
1. Check [docs/WORKSHOP-TEST-GUIDE.md](../docs/WORKSHOP-TEST-GUIDE.md)
2. Check [docs/TESTING-FINDINGS.md](../docs/TESTING-FINDINGS.md)
3. Review script comments and usage info
4. File an issue with script output

## Related Documentation

- [WORKSHOP-TEST-GUIDE.md](../docs/WORKSHOP-TEST-GUIDE.md) - Complete testing guide
- [TESTING-FINDINGS.md](../docs/TESTING-FINDINGS.md) - Known issues and recommendations
- [ENGINEERING.md](../docs/ENGINEERING.md) - Technical implementation details
- [DESIGN.md](../docs/DESIGN.md) - Workshop design and flow
- [README.md](../README.md) - Project overview
