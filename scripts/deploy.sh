#!/usr/bin/env bash
# =============================================================================
# deploy.sh - Deployment Simulation Script
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Simulates a CI/CD deployment by:
# 1. Updating the .env file with the new version
# 2. Pulling the image from the local registry
# 3. Restarting the service with docker-compose
# 4. Sending a deployment annotation to Elastic APM
# 5. Performing a health check
#
# Usage: ./deploy.sh <service-name> <version>
# Example: ./deploy.sh order-service v1.1-bad

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infra"
ENV_FILE="${INFRA_DIR}/.env"
COMPOSE_FILE="${INFRA_DIR}/docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Deployment metadata (simulated)
declare -A DEPLOYMENT_AUTHORS
DEPLOYMENT_AUTHORS["v1.0"]="platform-team"
DEPLOYMENT_AUTHORS["v1.1-bad"]="jordan.rivera"

declare -A DEPLOYMENT_COMMITS
DEPLOYMENT_COMMITS["v1.0"]="abc12345"
DEPLOYMENT_COMMITS["v1.1-bad"]="a1b2c3d4"

declare -A DEPLOYMENT_PRS
DEPLOYMENT_PRS["v1.0"]="PR-1200"
DEPLOYMENT_PRS["v1.1-bad"]="PR-1247"

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "==============================================================="
    echo "  DEPLOYMENT INITIATED"
    echo "==============================================================="
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

usage() {
    echo "Usage: $0 <service-name> <version>"
    echo ""
    echo "Services:"
    echo "  order-service      Java Spring Boot order processing"
    echo "  inventory-service  Python FastAPI inventory management"
    echo "  payment-service    Python FastAPI payment processing"
    echo ""
    echo "Versions:"
    echo "  v1.0       Good version (healthy)"
    echo "  v1.1-bad   Bad version (introduces latency bug)"
    echo ""
    echo "Example:"
    echo "  $0 order-service v1.1-bad"
    exit 1
}

validate_inputs() {
    local service=$1
    local version=$2

    # Validate service name
    case $service in
        order-service|inventory-service|payment-service)
            ;;
        *)
            print_error "Invalid service: $service"
            usage
            ;;
    esac

    # Validate version
    case $version in
        v1.0|v1.1-bad)
            ;;
        *)
            print_error "Invalid version: $version"
            usage
            ;;
    esac
}

update_env_file() {
    local service=$1
    local version=$2

    # Convert service name to env variable name
    local env_var
    case $service in
        order-service)
            env_var="ORDER_SERVICE_VERSION"
            ;;
        inventory-service)
            env_var="INVENTORY_SERVICE_VERSION"
            ;;
        payment-service)
            env_var="PAYMENT_SERVICE_VERSION"
            ;;
    esac

    print_info "Updating ${ENV_FILE}: ${env_var}=${version}"

    # Check if .env exists
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error ".env file not found at ${ENV_FILE}"
        print_info "Copy .env.example to .env and configure it first"
        exit 1
    fi

    # Update the version in .env file
    if grep -q "^${env_var}=" "$ENV_FILE"; then
        sed -i.bak "s/^${env_var}=.*/${env_var}=${version}/" "$ENV_FILE"
        rm -f "${ENV_FILE}.bak"
    else
        echo "${env_var}=${version}" >> "$ENV_FILE"
    fi

    print_success "Environment file updated"
}

pull_image() {
    local service=$1
    local version=$2

    # Load registry from .env
    source "$ENV_FILE"
    local registry="${REGISTRY:-localhost:5000}"

    print_info "Pulling image: ${registry}/${service}:${version}"

    if docker pull "${registry}/${service}:${version}" 2>/dev/null; then
        print_success "Image pulled successfully"
    else
        print_info "Image not in registry, will use local build"
    fi
}

restart_service() {
    local service=$1

    print_info "Restarting ${service} with docker-compose"

    cd "$INFRA_DIR"
    docker-compose up -d --no-deps "$service"

    print_success "Service restart initiated"
}

send_deployment_annotation() {
    local service=$1
    local version=$2

    # Load config from .env
    source "$ENV_FILE"

    local kibana_url="${KIBANA_URL}"
    local api_key="${ELASTIC_API_KEY}"
    local environment="${ENVIRONMENT:-local}"

    # Get deployment metadata
    local author="${DEPLOYMENT_AUTHORS[$version]:-unknown}"
    local commit="${DEPLOYMENT_COMMITS[$version]:-unknown}"
    local pr="${DEPLOYMENT_PRS[$version]:-unknown}"
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

    if [[ -z "$kibana_url" || -z "$api_key" ]]; then
        print_info "Kibana URL or API key not configured, skipping annotation"
        return 0
    fi

    print_info "Sending deployment annotation to Elastic APM"

    local response
    response=$(curl -s -w "\n%{http_code}" -X POST "${kibana_url}/api/apm/services/${service}/annotation" \
        -H "Authorization: ApiKey ${api_key}" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -d "{
            \"@timestamp\": \"${timestamp}\",
            \"service\": {
                \"name\": \"${service}\",
                \"version\": \"${version}\"
            },
            \"message\": \"Deployed ${version} by ${author}\",
            \"tags\": [\"deployment\", \"${environment}\", \"${pr}\"]
        }" 2>/dev/null || echo -e "\n000")

    local http_code
    http_code=$(echo "$response" | tail -n1)

    if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
        print_success "Deployment annotation sent"
    else
        print_info "Could not send annotation (HTTP ${http_code}), continuing anyway"
    fi
}

health_check() {
    local service=$1
    local port

    case $service in
        order-service)
            port=8080
            ;;
        inventory-service)
            port=8081
            ;;
        payment-service)
            port=8082
            ;;
    esac

    print_info "Waiting for ${service} to be healthy..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f "http://localhost:${port}/health" > /dev/null 2>&1; then
            print_success "Service is healthy"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done

    echo ""
    print_error "Service did not become healthy within 60 seconds"
    return 1
}

print_deployment_summary() {
    local service=$1
    local version=$2

    local author="${DEPLOYMENT_AUTHORS[$version]:-unknown}"
    local commit="${DEPLOYMENT_COMMITS[$version]:-unknown}"
    local pr="${DEPLOYMENT_PRS[$version]:-unknown}"
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)

    echo ""
    echo -e "${BLUE}===============================================================${NC}"
    echo -e "${GREEN}  DEPLOYMENT COMPLETE${NC}"
    echo -e "${BLUE}===============================================================${NC}"
    echo -e "  Service:     ${service}"
    echo -e "  Version:     ${version}"
    echo -e "  Timestamp:   ${timestamp}"
    echo -e "  Commit:      ${commit}"
    echo -e "  Author:      ${author}"
    echo -e "  PR:          ${pr}"
    echo -e "${BLUE}===============================================================${NC}"
    echo ""

    if [[ "$version" == "v1.1-bad" ]]; then
        echo -e "${YELLOW}NOTE: You deployed the 'bad' version. Watch for alerts in Kibana!${NC}"
        echo ""
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    if [[ $# -ne 2 ]]; then
        usage
    fi

    local service=$1
    local version=$2

    validate_inputs "$service" "$version"
    print_banner

    echo -e "  Service:     ${service}"
    echo -e "  Version:     ${version}"
    echo ""

    update_env_file "$service" "$version"
    pull_image "$service" "$version"
    restart_service "$service"
    send_deployment_annotation "$service" "$version"
    health_check "$service"
    print_deployment_summary "$service" "$version"
}

main "$@"
