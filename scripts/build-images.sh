#!/usr/bin/env bash
# =============================================================================
# build-images.sh - Build and Push Docker Images
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Builds all service Docker images and pushes them to the local registry.
# Creates both v1.0 (good) and v1.1-bad versions for Order Service.
#
# Usage: ./build-images.sh [--no-push] [--service <name>]

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/.."
SERVICES_DIR="${PROJECT_DIR}/services"
REGISTRY="${REGISTRY:-localhost:5000}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Flags
PUSH_TO_REGISTRY=true
SPECIFIC_SERVICE=""

# =============================================================================
# Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "==============================================================="
    echo "  BUILD DOCKER IMAGES"
    echo "==============================================================="
    echo -e "${NC}"
    echo "  Registry: ${REGISTRY}"
    echo ""
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
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --no-push              Build only, do not push to registry"
    echo "  --service <name>       Build only specified service"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Build and push all images"
    echo "  $0 --no-push           # Build only, no push"
    echo "  $0 --service order-service  # Build only order-service"
    exit 0
}

wait_for_registry() {
    if [[ "$PUSH_TO_REGISTRY" != "true" ]]; then
        return 0
    fi

    print_info "Checking registry availability..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -s "http://${REGISTRY}/v2/_catalog" > /dev/null 2>&1; then
            print_success "Registry is available"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done

    echo ""
    print_error "Registry not available at ${REGISTRY}"
    print_info "Start the registry with: docker-compose -f infra/docker-compose.yml up -d registry"
    exit 1
}

build_and_push() {
    local service=$1
    local dockerfile=$2
    local tag=$3

    local full_tag="${REGISTRY}/${service}:${tag}"
    local context="${SERVICES_DIR}/${service}"

    echo ""
    echo -e "${BLUE}Building ${service}:${tag}${NC}"
    echo "  Dockerfile: ${dockerfile}"
    echo "  Context:    ${context}"
    echo ""

    # Build the image
    if docker build -t "${full_tag}" -f "${context}/${dockerfile}" "${context}"; then
        print_success "Built ${full_tag}"
    else
        print_error "Failed to build ${full_tag}"
        return 1
    fi

    # Push to registry
    if [[ "$PUSH_TO_REGISTRY" == "true" ]]; then
        print_info "Pushing to registry..."
        if docker push "${full_tag}"; then
            print_success "Pushed ${full_tag}"
        else
            print_error "Failed to push ${full_tag}"
            return 1
        fi
    fi
}

build_order_service() {
    local service="order-service"

    echo ""
    echo -e "${BLUE}==============================${NC}"
    echo -e "${BLUE}Building Order Service${NC}"
    echo -e "${BLUE}==============================${NC}"

    # Check if service directory exists
    if [[ ! -d "${SERVICES_DIR}/${service}" ]]; then
        print_error "Service directory not found: ${SERVICES_DIR}/${service}"
        return 1
    fi

    # Build v1.0 (good version)
    build_and_push "${service}" "Dockerfile" "v1.0"

    # Build v1.1-bad (bad version with latency bug)
    if [[ -f "${SERVICES_DIR}/${service}/Dockerfile.bad" ]]; then
        build_and_push "${service}" "Dockerfile.bad" "v1.1-bad"
    else
        print_info "Dockerfile.bad not found, skipping v1.1-bad build"
    fi
}

build_python_service() {
    local service=$1

    echo ""
    echo -e "${BLUE}==============================${NC}"
    echo -e "${BLUE}Building ${service}${NC}"
    echo -e "${BLUE}==============================${NC}"

    # Check if service directory exists
    if [[ ! -d "${SERVICES_DIR}/${service}" ]]; then
        print_error "Service directory not found: ${SERVICES_DIR}/${service}"
        return 1
    fi

    # Build v1.0 (only version for Python services in main workshop)
    build_and_push "${service}" "Dockerfile" "v1.0"
}

build_all() {
    echo ""
    echo -e "${YELLOW}Building all services...${NC}"

    build_order_service
    build_python_service "inventory-service"
    build_python_service "payment-service"
    build_python_service "rollback-webhook"
}

print_summary() {
    echo ""
    echo -e "${BLUE}===============================================================${NC}"
    echo -e "${GREEN}  BUILD COMPLETE${NC}"
    echo -e "${BLUE}===============================================================${NC}"

    if [[ "$PUSH_TO_REGISTRY" == "true" ]]; then
        echo ""
        echo "Images available in registry:"
        curl -s "http://${REGISTRY}/v2/_catalog" 2>/dev/null | grep -o '"[^"]*"' | tr -d '"' | while read -r repo; do
            local tags
            tags=$(curl -s "http://${REGISTRY}/v2/${repo}/tags/list" 2>/dev/null | grep -o '"tags":\[[^]]*\]' | grep -o '"[^"]*"' | tr -d '"' | grep -v tags || echo "")
            if [[ -n "$tags" ]]; then
                for tag in $tags; do
                    echo "  - ${REGISTRY}/${repo}:${tag}"
                done
            fi
        done
    fi

    echo ""
    echo -e "${BLUE}===============================================================${NC}"
}

# =============================================================================
# Main
# =============================================================================

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-push)
            PUSH_TO_REGISTRY=false
            shift
            ;;
        --service)
            SPECIFIC_SERVICE=$2
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

print_banner
wait_for_registry

if [[ -n "$SPECIFIC_SERVICE" ]]; then
    case $SPECIFIC_SERVICE in
        order-service)
            build_order_service
            ;;
        inventory-service|payment-service|rollback-webhook)
            build_python_service "$SPECIFIC_SERVICE"
            ;;
        *)
            print_error "Unknown service: $SPECIFIC_SERVICE"
            exit 1
            ;;
    esac
else
    build_all
fi

print_summary
