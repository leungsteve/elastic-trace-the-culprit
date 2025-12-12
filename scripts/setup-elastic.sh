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

detect_data_format() {
    # Detect whether we're using OTLP direct ingestion or APM Server
    # This affects SLO threshold values due to unit conversion differences
    #
    # OTLP direct: histogram values in μs, but SLO multiplies threshold by 1000
    #              → Use threshold 500 for 500ms
    # APM Server:  normalizes to standard μs format
    #              → Use threshold 500000 for 500ms

    print_info "Detecting data format..."

    # Check for OTLP indices
    local otlp_count=0
    local apm_count=0

    # Query Elasticsearch for index counts
    local es_url="${ELASTIC_ENDPOINT:-${KIBANA_URL%:*}:9200}"

    # Try to detect based on indices (with timeout)
    local indices_response
    indices_response=$(curl -s --max-time 10 "${es_url}/_cat/indices/traces-*?h=index" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" 2>/dev/null || echo "")

    if echo "$indices_response" | grep -q "traces-generic.otel"; then
        otlp_count=1
    fi
    if echo "$indices_response" | grep -q "traces-apm"; then
        apm_count=1
    fi

    # Determine format based on what we found, or use DATA_FORMAT env var
    if [[ -n "${DATA_FORMAT:-}" ]]; then
        # Explicit override via environment variable
        print_info "Using DATA_FORMAT from environment: ${DATA_FORMAT}"
        echo "${DATA_FORMAT}"
    elif [[ $otlp_count -gt 0 && $apm_count -eq 0 ]]; then
        print_info "Detected OTLP data format (traces-generic.otel* indices)"
        echo "otlp"
    elif [[ $apm_count -gt 0 ]]; then
        print_info "Detected native APM data format (traces-apm* indices)"
        echo "apm"
    else
        # Default based on environment
        if [[ "${ENVIRONMENT:-local}" == "instruqt" ]]; then
            print_info "No indices found, defaulting to APM format for Instruqt"
            echo "apm"
        else
            print_info "No indices found, defaulting to OTLP format for local/cloud"
            echo "otlp"
        fi
    fi
}

set_slo_thresholds() {
    local data_format=$1

    if [[ "$data_format" == "otlp" ]]; then
        # OTLP: SLO transform multiplies by 1000, so use smaller value
        # 500 * 1000 = 500000 μs = 500ms
        export SLO_LATENCY_THRESHOLD=500
        export SLO_INDEX_PATTERN="traces-*,metrics-*"
        print_info "SLO config: threshold=${SLO_LATENCY_THRESHOLD}, index=${SLO_INDEX_PATTERN} (OTLP mode)"
    else
        # Native APM: sli.apm.transactionDuration uses milliseconds
        # 500 = 500ms
        # Index pattern must match APM transaction metrics data stream
        export SLO_LATENCY_THRESHOLD=500
        export SLO_INDEX_PATTERN="metrics-apm.transaction.1m*"
        print_info "SLO config: threshold=${SLO_LATENCY_THRESHOLD}ms, index=${SLO_INDEX_PATTERN} (APM mode)"
    fi
}

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
    local var_name=$3

    print_info "Creating SLO: ${name}"

    if [[ ! -f "$file" ]]; then
        print_error "SLO file not found: ${file}"
        return 1
    fi

    local data
    data=$(cat "$file")

    # Substitute environment-specific values
    data=$(echo "$data" | sed "s|{{SLO_LATENCY_THRESHOLD}}|${SLO_LATENCY_THRESHOLD:-500000}|g")
    data=$(echo "$data" | sed "s|{{SLO_INDEX_PATTERN}}|${SLO_INDEX_PATTERN:-traces-*,metrics-*}|g")

    local response
    if response=$(api_call POST "/api/observability/slos" "$data"); then
        print_success "Created SLO: ${name}"

        # Extract SLO ID from response
        local slo_id
        slo_id=$(echo "$response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

        if [[ -n "$slo_id" && -n "$var_name" ]]; then
            eval "${var_name}='${slo_id}'"
            print_info "SLO ID: ${slo_id}"
        fi
    else
        print_info "SLO may already exist or there was an error"
    fi
}

rule_exists() {
    local name=$1
    local response
    response=$(curl -s -X GET "${KIBANA_URL}/api/alerting/rules/_find?search=${name// /%20}&per_page=100" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "kbn-xsrf: true" 2>/dev/null)
    
    # Check if a rule with exact name exists
    echo "$response" | jq -e ".data[] | select(.name == \"${name}\")" > /dev/null 2>&1
}

create_rule() {
    local name=$1
    local file=$2
    shift 2
    # Remaining args are key=value pairs for substitution

    print_info "Creating alert rule: ${name}"

    # Check if rule already exists
    if rule_exists "$name"; then
        print_info "Rule '${name}' already exists - skipping"
        return 0
    fi

    if [[ ! -f "$file" ]]; then
        print_error "Rule file not found: ${file}"
        return 1
    fi

    local data
    data=$(cat "$file")

    # Perform substitutions for all passed key=value pairs
    for arg in "$@"; do
        local key="${arg%%=*}"
        local value="${arg#*=}"
        data=$(echo "$data" | sed "s|{{${key}}}|${value}|g")
    done

    # Debug: Show payload if DEBUG=true
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${YELLOW}DEBUG: Payload for ${name}:${NC}"
        echo "$data" | jq '.' 2>/dev/null || echo "$data"
    fi

    # Make API call with full response capture
    local url="${KIBANA_URL}/api/alerting/rule"
    local response
    response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -d "$data" 2>&1)

    local http_code
    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
        local rule_id
        rule_id=$(echo "$body" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
        print_success "Created rule: ${name} (ID: ${rule_id})"
        return 0
    elif [[ "$http_code" == "409" ]]; then
        print_info "Rule '${name}' already exists"
        return 0
    else
        print_error "Failed to create rule '${name}': HTTP ${http_code}"
        # Show error details
        local error_msg
        error_msg=$(echo "$body" | jq -r '.message // .error // .' 2>/dev/null || echo "$body")
        print_error "Error: ${error_msg}"
        return 1
    fi
}

create_connector() {
    local name=$1
    local file=$2
    local var_name=$3

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
        print_info "WEBHOOK_PUBLIC_URL not set, skipping connector creation"
        return 0
    fi

    local response
    if response=$(api_call POST "/api/actions/connector" "$data"); then
        print_success "Created connector: ${name}"

        # Extract connector ID from response
        local connector_id
        connector_id=$(echo "$response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

        if [[ -n "$connector_id" && -n "$var_name" ]]; then
            eval "${var_name}='${connector_id}'"
            print_info "Connector ID: ${connector_id}"
        fi
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

    create_slo "Order Service Latency" "${ASSETS_DIR}/slos/order-latency.json" ORDER_LATENCY_SLO_ID
    create_slo "Order Service Availability" "${ASSETS_DIR}/slos/order-availability.json" ORDER_AVAILABILITY_SLO_ID
}

setup_alerts() {
    echo ""
    echo -e "${BLUE}Setting up Alert Rules...${NC}"
    echo ""

    # Create latency threshold alert
    create_rule "Latency Threshold" "${ASSETS_DIR}/alerts/latency-threshold.json"

    # Create SLO burn rate alert with dynamic SLO ID substitution
    if [[ -n "$ORDER_LATENCY_SLO_ID" ]]; then
        create_rule "SLO Burn Rate" "${ASSETS_DIR}/alerts/slo-burn-rate.json" \
            "ORDER_LATENCY_SLO_ID=${ORDER_LATENCY_SLO_ID}"
    else
        print_info "Skipping SLO Burn Rate alert (ORDER_LATENCY_SLO_ID not set)"
    fi
}

setup_connectors() {
    echo ""
    echo -e "${BLUE}Setting up Connectors...${NC}"
    echo ""

    create_connector "Rollback Webhook" "${ASSETS_DIR}/workflows/webhook-connector.json" WEBHOOK_CONNECTOR_ID
}

setup_dashboard() {
    echo ""
    echo -e "${BLUE}Setting up Dashboard...${NC}"
    echo ""

    import_dashboard "${ASSETS_DIR}/dashboards/workshop-overview.ndjson"
}

# =============================================================================
# ML Job Functions (uses Elasticsearch API directly)
# =============================================================================

ml_job_exists() {
    local job_id=$1
    local response
    response=$(curl -s "${ELASTIC_ENDPOINT}/_ml/anomaly_detectors/${job_id}" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" 2>/dev/null)
    
    # Check if job exists (not an error response)
    echo "$response" | jq -e ".jobs[0].job_id == \"${job_id}\"" > /dev/null 2>&1
}

create_ml_job() {
    local job_id=$1
    local file=$2

    print_info "Creating ML job: ${job_id}"

    if [[ -z "$ELASTIC_ENDPOINT" ]]; then
        print_info "ELASTIC_ENDPOINT not set, skipping ML job creation"
        return 0
    fi

    # Check if job already exists
    if ml_job_exists "$job_id"; then
        print_info "ML job '${job_id}' already exists - skipping"
        return 0
    fi

    if [[ ! -f "$file" ]]; then
        print_error "ML job file not found: ${file}"
        return 1
    fi

    local data
    data=$(cat "$file")

    # Extract just the job configuration (remove non-API fields)
    local job_config
    job_config=$(echo "$data" | jq '{
        description: .description,
        analysis_config: .analysis_config,
        data_description: .data_description,
        analysis_limits: (.analysis_limits // {model_memory_limit: "128mb"}),
        model_plot_config: (.model_plot_config // {enabled: true})
    }')

    # Debug: Show payload if DEBUG=true
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${YELLOW}DEBUG: ML Job payload for ${job_id}:${NC}"
        echo "$job_config" | jq '.'
    fi

    # Create the ML job via Elasticsearch API
    local response
    response=$(curl -s -w "\n%{http_code}" -X PUT "${ELASTIC_ENDPOINT}/_ml/anomaly_detectors/${job_id}" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$job_config" 2>&1)

    local http_code
    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
        print_success "Created ML job: ${job_id}"
        
        # Create datafeed if specified in the file
        local datafeed_config
        datafeed_config=$(echo "$data" | jq '.datafeed_config // empty')
        
        if [[ -n "$datafeed_config" && "$datafeed_config" != "null" ]]; then
            local datafeed_id
            datafeed_id=$(echo "$datafeed_config" | jq -r '.datafeed_id')
            
            # Remove datafeed_id from config (it's in the URL) and add job_id
            datafeed_config=$(echo "$datafeed_config" | jq --arg jid "$job_id" 'del(.datafeed_id) | .job_id = $jid')
            
            print_info "Creating datafeed: ${datafeed_id}"
            
            local df_response
            df_response=$(curl -s -w "\n%{http_code}" -X PUT "${ELASTIC_ENDPOINT}/_ml/datafeeds/${datafeed_id}" \
                -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
                -H "Content-Type: application/json" \
                -d "$datafeed_config" 2>&1)
            
            local df_code
            df_code=$(echo "$df_response" | tail -n1)
            
            if [[ "$df_code" == "200" || "$df_code" == "201" ]]; then
                print_success "Created datafeed: ${datafeed_id}"
                
                # Open the job before starting datafeed
                curl -s -X POST "${ELASTIC_ENDPOINT}/_ml/anomaly_detectors/${job_id}/_open" \
                    -H "Authorization: ApiKey ${ELASTIC_API_KEY}" > /dev/null 2>&1
                
                # Start the datafeed
                curl -s -X POST "${ELASTIC_ENDPOINT}/_ml/datafeeds/${datafeed_id}/_start" \
                    -H "Authorization: ApiKey ${ELASTIC_API_KEY}" > /dev/null 2>&1
                
                print_success "Started datafeed: ${datafeed_id}"
            else
                local df_error
                df_error=$(echo "$df_response" | sed '$d' | jq -r '.error.reason // .message // .' 2>/dev/null)
                print_info "Datafeed creation issue: ${df_error}"
            fi
        fi
        return 0
    else
        print_error "Failed to create ML job '${job_id}': HTTP ${http_code}"
        local error_msg
        error_msg=$(echo "$body" | jq -r '.error.reason // .message // .' 2>/dev/null || echo "$body")
        print_error "Error: ${error_msg}"
        return 1
    fi
}

setup_ml_jobs() {
    echo ""
    echo -e "${BLUE}Setting up ML Jobs...${NC}"
    echo ""

    create_ml_job "apm-order-service-latency-anomaly" \
        "${ASSETS_DIR}/ml-jobs/apm-latency-anomaly.json"
}

# Note: Agent Builder tools are now created via Python scripts
# See scripts/create-agent-builder-tools.py for the working implementation
# This function is kept for reference but should not be called

# Note: Agent Builder agent is now created via Python scripts
# See scripts/deploy-agent-builder.py for the working implementation
# This function is kept for reference but should not be called

index_deployment_metadata() {
    local metadata_file=$1

    if [[ -z "$ELASTIC_ENDPOINT" ]]; then
        print_info "ELASTIC_ENDPOINT not set, skipping deployment metadata indexing"
        return 0
    fi

    if [[ ! -f "$metadata_file" ]]; then
        print_info "Deployment metadata file not found: ${metadata_file}"
        return 0
    fi

    print_info "Indexing deployment metadata"

    local metadata_data
    metadata_data=$(cat "$metadata_file")

    # Replace placeholder timestamp with current time
    local current_timestamp
    current_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
    metadata_data=$(echo "$metadata_data" | sed "s|{{DEPLOYMENT_TIMESTAMP}}|${current_timestamp}|g")

    # Create index if it doesn't exist and index the document
    local index_name="deployment-metadata"
    local doc_id="order-service-v1.1-bad"

    # Try to index the document
    local url="${ELASTIC_ENDPOINT}/${index_name}/_doc/${doc_id}"
    
    local response
    response=$(curl -s -w "\n%{http_code}" -X PUT "$url" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$metadata_data" 2>/dev/null || echo -e "\n000")

    local http_code
    http_code=$(echo "$response" | tail -n1)

    if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
        print_success "Indexed deployment metadata"
        return 0
    else
        print_info "Deployment metadata indexing failed (HTTP ${http_code}), continuing..."
        return 0  # Non-fatal, continue setup
    fi
}

setup_workflows() {
    echo ""
    echo -e "${BLUE}Setting up Workflows...${NC}"
    echo ""

    # Enable Workflows UI
    print_info "Enabling Workflows UI..."
    local response
    response=$(curl -s -w "\n%{http_code}" -X POST "${KIBANA_URL}/internal/kibana/settings" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -H "elastic-api-version: 1" \
        -d '{"changes":{"workflows:ui:enabled":true}}' 2>/dev/null || echo -e "\n000")

    local http_code
    http_code=$(echo "$response" | tail -n1)

    if [[ "$http_code" == "200" ]]; then
        print_success "Workflows UI enabled"
    else
        print_info "Workflows UI may already be enabled or not available (HTTP ${http_code})"
    fi

    # Create workflow YAML file for manual import
    local workflow_file="${ASSETS_DIR}/workflows/auto-rollback-workflow.yaml"
    print_info "Creating workflow definition file..."

    cat > "$workflow_file" << 'EOF'
name: auto-rollback-on-latency
description: Automatically triggers rollback when SLO burn rate alert fires
triggers:
  - type: alert
steps:
  - name: trigger_rollback
    type: http
    with:
      url: "http://host-1:9000/rollback"
      method: "POST"
      headers:
        Content-Type: "application/json"
      body:
        service: "order-service"
        target_version: "v1.0"
        alert_id: "{{ alert.id }}"
        reason: "SLO burn rate alert triggered automatic rollback"
EOF

    print_success "Workflow YAML saved to: ${workflow_file}"
    echo ""
    print_info "To create the workflow:"
    print_info "  1. Go to Kibana → Management → Workflows"
    print_info "  2. Click 'Create Workflow'"
    print_info "  3. Paste the YAML from: ${workflow_file}"
    print_info "  4. Save the workflow"
    print_info "  5. Configure SLO Burn Rate alert to use 'Run Workflow' action"
}

setup_agent_builder() {
    echo ""
    echo -e "${BLUE}Setting up Agent Builder...${NC}"
    echo ""

    local metadata_file="${ASSETS_DIR}/deployment-metadata/v1.1-bad-changes.json"

    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required for Agent Builder setup"
        print_info "Skipping Agent Builder setup"
        return 1
    fi

    # Step 1: Deploy the agent
    print_info "Creating Agent Builder agent..."
    if python3 "${SCRIPT_DIR}/deploy-agent-builder.py" 2>&1 | grep -q "DEPLOYMENT COMPLETE\|already exists"; then
        print_success "Agent created: NovaMart Incident Investigation Assistant"
    else
        print_info "Agent deployment status unknown (may already exist)"
    fi

    echo ""

    # Step 2: Create custom tools
    print_info "Creating custom Agent Builder tools..."
    if python3 "${SCRIPT_DIR}/create-agent-builder-tools.py" 2>&1 | grep -q "ALL TOOLS CREATED SUCCESSFULLY"; then
        print_success "Created 8 custom ES|QL tools"
    else
        print_info "Tool creation status unknown (may already exist)"
    fi

    echo ""

    # Step 3: Update agent with tools
    print_info "Configuring agent with custom tools..."
    if python3 "${SCRIPT_DIR}/update-agent-tools.py" 2>&1 | grep -q "AGENT UPDATE COMPLETE"; then
        print_success "Agent configured with 15 tools (8 custom + 7 built-in)"
    else
        print_info "Agent configuration status unknown"
    fi

    echo ""

    # Step 4: Index deployment metadata
    if [[ -f "$metadata_file" ]]; then
        print_info "Indexing deployment metadata..."
        if index_deployment_metadata "$metadata_file"; then
            print_success "Deployment metadata indexed"
        else
            print_info "Deployment metadata indexing may have failed"
        fi
    else
        print_error "Deployment metadata file not found: ${metadata_file}"
    fi

    echo ""
    print_success "Agent Builder setup complete"
    echo ""
    print_info "Access the agent at:"
    print_info "  Kibana → Search → AI Assistants"
    print_info "  Agent: NovaMart Incident Investigation Assistant"
    echo ""
    print_info "For troubleshooting, see: README-AGENT-BUILDER.md"
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
    echo "  - Workflows UI enabled + workflow YAML created"
    echo "  - ML anomaly detection job"
    echo "  - Webhook connector for rollback (if WEBHOOK_PUBLIC_URL set)"
    echo "  - Agent Builder tools and agent"
    echo "  - Deployment metadata (indexed)"
    echo "  - Workshop dashboard"
    echo ""
    echo "Next steps:"
    echo "  1. Verify assets in Kibana"
    echo "  2. Access Agent Builder: Search > AI Assistants or Agent Builder"
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

    # Detect data format and set appropriate thresholds
    local data_format
    data_format=$(detect_data_format)
    set_slo_thresholds "$data_format"

    # Create connectors first (needed for alert actions)
    setup_connectors

    # Create SLOs (needed for SLO burn rate alert)
    setup_slos

    # Create alert rules (can now reference SLO IDs and connector IDs)
    setup_alerts

    # Enable Workflows and create workflow definition
    setup_workflows

    # Create ML jobs for anomaly detection
    setup_ml_jobs

    # Import dashboard and setup agent builder
    setup_dashboard
    setup_agent_builder

    print_summary
}

main "$@"
