# Contributing to From Commit to Culprit

Thank you for your interest in contributing to this Elastic Observability workshop!

## Development Setup

### Prerequisites

- Docker 24.x and Docker Compose 2.x
- Java 21 (for Order Service development)
- Python 3.11 (for Python services development)
- curl and bash
- An Elastic Cloud account or local Elastic stack

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/from-commit-to-culprit.git
cd from-commit-to-culprit

# Start Elastic locally
curl -fsSL https://elastic.co/start-local | sh

# Copy and configure environment
cp infra/.env.example infra/.env
# Edit .env with your Elastic endpoint and API key

# Build images and start services
./scripts/build-images.sh
docker-compose -f infra/docker-compose.yml up -d

# Provision Elastic assets
./scripts/setup-elastic.sh

# Generate baseline traffic
./scripts/load-generator.sh &

# Verify everything is working
./scripts/health-check.sh
```

### Testing Your Changes

Before submitting a PR, test the full workshop flow:

```bash
# Deploy bad code
./scripts/deploy.sh order-service v1.1-bad

# Verify in Kibana:
# 1. Latency spikes in APM
# 2. SLO burn rate increases
# 3. Alert fires
# 4. Workflow triggers rollback
# 5. Service recovers
```

## Code Style Guidelines

### Java (Order Service)

- Follow [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- Use meaningful variable and method names
- Include Javadoc comments for public methods
- Format code with `google-java-format`

### Python (Inventory, Payment, Webhook Services)

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for function parameters and return values
- Use docstrings for modules, classes, and functions
- Format code with `black` and lint with `ruff`

### Shell Scripts

- Use [shellcheck](https://www.shellcheck.net/) for linting
- Include error handling (`set -e`)
- Add comments explaining non-obvious logic
- Use meaningful variable names

### All Code

- Include comments explaining workshop context (why this code exists)
- Keep code simple and readable (this is educational material)
- Avoid over-engineering

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Scopes

- `order-service`: Order Service changes
- `inventory-service`: Inventory Service changes
- `payment-service`: Payment Service changes
- `webhook`: Rollback Webhook changes
- `infra`: Infrastructure (Docker, compose, etc.)
- `scripts`: Shell scripts
- `elastic-assets`: Elastic configuration files
- `instruqt`: Instruqt track and challenges
- `docs`: Documentation

### Examples

```
feat(order-service): add custom span for detailed trace logging
fix(deploy): correct version extraction from .env
docs(readme): update architecture diagram
test(telemetry): add trace correlation validation
refactor(payment-service): simplify payment validation logic
chore(infra): update EDOT collector to 8.17.0
```

## Testing Requirements

Before submitting a PR, ensure:

### Unit Tests

```bash
# Java
cd services/order-service && ./mvnw test

# Python
cd services/inventory-service && pytest
cd services/payment-service && pytest
cd services/rollback-webhook && pytest
```

### Integration Tests

```bash
./scripts/run-tests.sh integration
```

### Manual Testing

1. Start all services with `docker-compose up`
2. Run the load generator
3. Deploy bad code and verify alert fires
4. Verify rollback works
5. Check all Kibana views show expected data

## Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following the style guidelines
3. **Write tests** for new functionality
4. **Update documentation** if needed
5. **Test locally** using the full workshop flow
6. **Submit PR** with a clear description

### PR Description Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Infrastructure change

## Testing
Describe how you tested these changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated (if needed)
- [ ] Workshop flow tested end-to-end
```

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- For Elastic-specific questions, visit [Elastic Community](https://discuss.elastic.co/)
