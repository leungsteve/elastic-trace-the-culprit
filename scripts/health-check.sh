#!/usr/bin/env bash
# =============================================================================
# health-check.sh - Service Health Check Script
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Checks the health of all workshop services and reports their status.
#
# Usage: ./health-check.sh

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infra"
ENV_FILE="${INFRA_DIR}/.env"

# Service endpoints
declare -A SERVICES
SERVICES["order-service"]="http://localhost:8088"
SERVICES["inventory-service"]="http://localhost:8081"
SERVICES["payment-service"]="http://localhost:8082"
SERVICES["rollback-webhook"]="http://localhost:9000"
SERVICES["otel-collector"]="http://localhost:13133"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
HEALTHY=0
UNHEALTHY=0

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "==============================================================="
    echo "  WORKSHOP HEALTH CHECK"
    echo "==============================================================="
    echo -e "${NC}"
}

check_service() {
    local name=$1
    local url=$2
    local health_endpoint="${url}/health"

    # Special case for OTEL collector
    if [[ "$name" == "otel-collector" ]]; then
        health_endpoint="${url}"
    fi

    printf "  %-20s " "${name}:"

    local response
    local http_code

    response=$(curl -s -w "\n%{http_code}" -m 5 "${health_endpoint}" 2>/dev/null || echo -e "\n000")
    http_code=$(echo "$response" | tail -n1)

    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}HEALTHY${NC}"
        ((HEALTHY++))
        return 0
    else
        echo -e "${RED}UNHEALTHY${NC} (HTTP ${http_code})"
        ((UNHEALTHY++))
        return 1
    fi
}

check_docker() {
    printf "  %-20s " "Docker:"

    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}RUNNING${NC}"
        return 0
    else
        echo -e "${RED}NOT RUNNING${NC}"
        return 1
    fi
}

check_containers() {
    echo ""
    echo -e "${BLUE}Container Status:${NC}"
    echo ""

    cd "$INFRA_DIR"

    if [[ -f docker-compose.yml ]]; then
        docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || \
            docker-compose ps 2>/dev/null || \
            echo "  Could not get container status"
    else
        echo "  docker-compose.yml not found"
    fi
}

check_elastic_connection() {
    echo ""
    echo -e "${BLUE}Elastic Connection:${NC}"
    echo ""

    if [[ -f "$ENV_FILE" ]]; then
        source "$ENV_FILE"
    fi

    printf "  %-20s " "Elastic Endpoint:"

    if [[ -z "$ELASTIC_ENDPOINT" ]]; then
        echo -e "${YELLOW}NOT CONFIGURED${NC}"
        return 1
    fi

    # Try to connect to Elastic
    local response
    response=$(curl -s -w "\n%{http_code}" -m 10 \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        "${ELASTIC_ENDPOINT}" 2>/dev/null || echo -e "\n000")

    local http_code
    http_code=$(echo "$response" | tail -n1)

    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}CONNECTED${NC}"
        return 0
    else
        echo -e "${RED}NOT CONNECTED${NC} (HTTP ${http_code})"
        return 1
    fi
}

check_registry() {
    echo ""
    echo -e "${BLUE}Container Registry:${NC}"
    echo ""

    printf "  %-20s " "Registry:"

    local response
    response=$(curl -s -w "\n%{http_code}" -m 5 "http://localhost:5000/v2/_catalog" 2>/dev/null || echo -e "\n000")
    local http_code
    http_code=$(echo "$response" | tail -n1)

    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}RUNNING${NC}"

        # List available images
        local catalog
        catalog=$(echo "$response" | sed '$d')
        echo ""
        echo "  Available images:"
        echo "$catalog" | grep -o '"[^"]*"' | tr -d '"' | while read -r repo; do
            # Get tags for each repo
            local tags
            tags=$(curl -s "http://localhost:5000/v2/${repo}/tags/list" 2>/dev/null | grep -o '"tags":\[[^]]*\]' | grep -o '"[^"]*"' | tr -d '"' | grep -v tags || echo "")
            if [[ -n "$tags" ]]; then
                for tag in $tags; do
                    echo "    - ${repo}:${tag}"
                done
            fi
        done
        return 0
    else
        echo -e "${RED}NOT RUNNING${NC}"
        return 1
    fi
}

print_summary() {
    echo ""
    echo -e "${BLUE}===============================================================${NC}"
    echo -e "${BLUE}  SUMMARY${NC}"
    echo -e "${BLUE}===============================================================${NC}"
    echo -e "  Healthy Services:   ${GREEN}${HEALTHY}${NC}"
    echo -e "  Unhealthy Services: ${RED}${UNHEALTHY}${NC}"
    echo -e "${BLUE}===============================================================${NC}"

    if [[ $UNHEALTHY -gt 0 ]]; then
        echo ""
        echo -e "${YELLOW}Some services are unhealthy. Check the logs with:${NC}"
        echo "  docker-compose -f ${INFRA_DIR}/docker-compose.yml logs <service-name>"
        echo ""
        return 1
    else
        echo ""
        echo -e "${GREEN}All services are healthy!${NC}"
        echo ""
        return 0
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    print_banner

    echo -e "${BLUE}Prerequisites:${NC}"
    echo ""
    check_docker || true

    echo ""
    echo -e "${BLUE}Service Health:${NC}"
    echo ""

    for service in "${!SERVICES[@]}"; do
        check_service "$service" "${SERVICES[$service]}" || true
    done

    check_containers
    check_elastic_connection || true
    check_registry || true

    print_summary
}

main "$@"
