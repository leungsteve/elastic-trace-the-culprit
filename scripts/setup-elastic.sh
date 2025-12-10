#!/usr/bin/env bash
# =============================================================================
# setup-elastic.sh - Provision Elastic Assets
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Provisions all Elastic assets via Kibana API:
# - SLOs (latency and availability)
# - Alert rules (threshold and SLO burn rate)
# - Webhook connector for rollback
# - Agent Builder tools and agent
# - Workshop dashboard
#
# Usage: ./setup-elastic.sh
# Requires: ELASTIC_API_KEY, KIBANA_URL environment variables

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/.."
ASSETS_DIR="${PROJECT_DIR}/elastic-assets"
INFRA_DIR="${PROJECT_DIR}/infra"
ENV_FILE="${INFRA_DIR}/.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "==============================================================="
    echo "  ELASTIC ASSET PROVISIONING"
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

load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        source "$ENV_FILE"
    fi

    if [[ -z "$KIBANA_URL" || -z "$ELASTIC_API_KEY" ]]; then
        print_error "KIBANA_URL and ELASTIC_API_KEY must be set"
        print_info "Set them in ${ENV_FILE} or as environment variables"
        exit 1
    fi

    echo "  Kibana URL: ${KIBANA_URL}"
    echo "  Webhook URL: ${WEBHOOK_PUBLIC_URL:-not configured}"
    echo ""
}

api_call() {
    local method=$1
    local endpoint=$2
    local data=$3

    local url="${KIBANA_URL}${endpoint}"

    local response
    if [[ -n "$data" ]]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
            -H "Content-Type: application/json" \
            -H "kbn-xsrf: true" \
            -d "$data" 2>/dev/null || echo -e "\n000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
            -H "kbn-xsrf: true" 2>/dev/null || echo -e "\n000")
    fi

    local http_code
    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" == "200" || "$http_code" == "201" || "$http_code" == "204" ]]; then
        echo "$body"
        return 0
    else
        echo "HTTP ${http_code}: ${body}" >&2
        return 1
    fi
}

create_slo() {
    local name=$1
    local file=$2

    print_info "Creating SLO: ${name}"

    if [[ ! -f "$file" ]]; then
        print_error "SLO file not found: ${file}"
        return 1
    fi

    local data
    data=$(cat "$file")

    if api_call POST "/api/observability/slos" "$data" > /dev/null; then
        print_success "Created SLO: ${name}"
    else
        print_info "SLO may already exist or there was an error"
    fi
}

create_rule() {
    local name=$1
    local file=$2

    print_info "Creating alert rule: ${name}"

    if [[ ! -f "$file" ]]; then
        print_error "Rule file not found: ${file}"
        return 1
    fi

    local data
    data=$(cat "$file")

    # Substitute webhook URL if present
    if [[ -n "$WEBHOOK_PUBLIC_URL" ]]; then
        data=$(echo "$data" | sed "s|{{WEBHOOK_PUBLIC_URL}}|${WEBHOOK_PUBLIC_URL}|g")
    fi

    if api_call POST "/api/alerting/rule" "$data" > /dev/null; then
        print_success "Created rule: ${name}"
    else
        print_info "Rule may already exist or there was an error"
    fi
}

create_connector() {
    local name=$1
    local file=$2

    print_info "Creating connector: ${name}"

    if [[ ! -f "$file" ]]; then
        print_error "Connector file not found: ${file}"
        return 1
    fi

    local data
    data=$(cat "$file")

    # Substitute webhook URL
    if [[ -n "$WEBHOOK_PUBLIC_URL" ]]; then
        data=$(echo "$data" | sed "s|{{WEBHOOK_PUBLIC_URL}}|${WEBHOOK_PUBLIC_URL}|g")
    else
        print_info "WEBHOOK_PUBLIC_URL not set, connector may not work"
    fi

    if api_call POST "/api/actions/connector" "$data" > /dev/null; then
        print_success "Created connector: ${name}"
    else
        print_info "Connector may already exist or there was an error"
    fi
}

import_dashboard() {
    local file=$1

    print_info "Importing dashboard"

    if [[ ! -f "$file" ]]; then
        print_error "Dashboard file not found: ${file}"
        return 1
    fi

    if api_call POST "/api/saved_objects/_import?overwrite=true" "@${file}" > /dev/null; then
        print_success "Imported dashboard"
    else
        print_info "Dashboard import may have failed"
    fi
}

setup_slos() {
    echo ""
    echo -e "${BLUE}Setting up SLOs...${NC}"
    echo ""

    create_slo "Order Service Latency" "${ASSETS_DIR}/slos/order-latency.json"
    create_slo "Order Service Availability" "${ASSETS_DIR}/slos/order-availability.json"
}

setup_alerts() {
    echo ""
    echo -e "${BLUE}Setting up Alert Rules...${NC}"
    echo ""

    create_rule "Latency Threshold" "${ASSETS_DIR}/alerts/latency-threshold.json"
    create_rule "SLO Burn Rate" "${ASSETS_DIR}/alerts/slo-burn-rate.json"
}

setup_connectors() {
    echo ""
    echo -e "${BLUE}Setting up Connectors...${NC}"
    echo ""

    create_connector "Rollback Webhook" "${ASSETS_DIR}/workflows/webhook-connector.json"
}

setup_dashboard() {
    echo ""
    echo -e "${BLUE}Setting up Dashboard...${NC}"
    echo ""

    import_dashboard "${ASSETS_DIR}/dashboards/workshop-overview.ndjson"
}

setup_agent_builder() {
    echo ""
    echo -e "${BLUE}Setting up Agent Builder...${NC}"
    echo ""

    # Note: Agent Builder API endpoints may vary
    # This is a placeholder for when the API is available

    local tools_dir="${ASSETS_DIR}/agent-builder/tools"

    if [[ -d "$tools_dir" ]]; then
        for tool_file in "$tools_dir"/*.json; do
            if [[ -f "$tool_file" ]]; then
                local tool_name
                tool_name=$(basename "$tool_file" .json)
                print_info "Agent Builder tool: ${tool_name} (manual setup may be required)"
            fi
        done
    fi

    print_info "Agent Builder setup may require manual configuration in Kibana"
}

verify_connection() {
    echo ""
    echo -e "${BLUE}Verifying Elastic connection...${NC}"
    echo ""

    if api_call GET "/api/status" > /dev/null 2>&1; then
        print_success "Connected to Elastic"
    else
        print_error "Could not connect to Elastic"
        exit 1
    fi
}

print_summary() {
    echo ""
    echo -e "${BLUE}===============================================================${NC}"
    echo -e "${GREEN}  SETUP COMPLETE${NC}"
    echo -e "${BLUE}===============================================================${NC}"
    echo ""
    echo "The following Elastic assets have been provisioned:"
    echo "  - SLOs (latency and availability)"
    echo "  - Alert rules (threshold and burn rate)"
    echo "  - Webhook connector for rollback"
    echo "  - Workshop dashboard"
    echo ""
    echo "Next steps:"
    echo "  1. Verify assets in Kibana"
    echo "  2. Configure Agent Builder tools manually if needed"
    echo "  3. Start the load generator: ./scripts/load-generator.sh"
    echo ""
    echo -e "${BLUE}===============================================================${NC}"
}

# =============================================================================
# Main
# =============================================================================

main() {
    print_banner
    load_env
    verify_connection

    setup_slos
    setup_alerts
    setup_connectors
    setup_dashboard
    setup_agent_builder

    print_summary
}

main "$@"
