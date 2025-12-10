#!/usr/bin/env bash
# =============================================================================
# setup-registry.sh - Local Docker Registry Setup
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Starts and verifies the local Docker registry for workshop images.
# The registry allows fast image pulling and deployment during the workshop.
#
# Usage: ./setup-registry.sh

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infra"
COMPOSE_FILE="${INFRA_DIR}/docker-compose.yml"
REGISTRY_URL="localhost:5000"
MAX_WAIT_TIME=30

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
    echo "  LOCAL DOCKER REGISTRY SETUP"
    echo "==============================================================="
    echo -e "${NC}"
    echo "  Registry URL: ${REGISTRY_URL}"
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

check_docker() {
    print_info "Checking Docker..."

    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    print_success "Docker is running"
}

check_compose_file() {
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_error "docker-compose.yml not found at ${COMPOSE_FILE}"
        exit 1
    fi
}

start_registry() {
    print_info "Starting registry container..."
    echo ""

    cd "$INFRA_DIR"

    # Start only the registry service
    if docker-compose up -d registry; then
        print_success "Registry container started"
    else
        print_error "Failed to start registry container"
        exit 1
    fi
}

wait_for_registry() {
    print_info "Waiting for registry to become healthy..."

    local attempt=1
    local endpoint="http://${REGISTRY_URL}/v2/_catalog"

    while [[ $attempt -le $MAX_WAIT_TIME ]]; do
        if curl -s "$endpoint" > /dev/null 2>&1; then
            echo ""
            print_success "Registry is healthy and responding"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done

    echo ""
    print_error "Registry failed to become healthy after ${MAX_WAIT_TIME} seconds"
    print_info "Check logs with: docker logs registry"
    exit 1
}

verify_registry() {
    print_info "Verifying registry accessibility..."

    local catalog
    catalog=$(curl -s "http://${REGISTRY_URL}/v2/_catalog" 2>/dev/null)

    if [[ $? -eq 0 ]]; then
        print_success "Registry is accessible at ${REGISTRY_URL}"

        # Check if there are any images in the registry
        local image_count
        image_count=$(echo "$catalog" | grep -o '"[^"]*"' | grep -v repositories | wc -l | tr -d ' ')

        if [[ "$image_count" -gt 0 ]]; then
            echo ""
            echo -e "${BLUE}Existing images in registry:${NC}"
            echo "$catalog" | grep -o '"[^"]*"' | tr -d '"' | grep -v repositories | while read -r repo; do
                # Get tags for each repo
                local tags
                tags=$(curl -s "http://${REGISTRY_URL}/v2/${repo}/tags/list" 2>/dev/null | grep -o '"tags":\[[^]]*\]' | grep -o '"[^"]*"' | tr -d '"' | grep -v tags || echo "")
                if [[ -n "$tags" ]]; then
                    for tag in $tags; do
                        echo "  - ${repo}:${tag}"
                    done
                fi
            done
        else
            echo ""
            print_info "Registry is empty. Run build-images.sh to populate it."
        fi
    else
        print_error "Registry is not accessible at ${REGISTRY_URL}"
        exit 1
    fi
}

check_registry_container() {
    print_info "Checking registry container status..."

    if docker ps --filter "name=registry" --format "{{.Names}}" | grep -q "^registry$"; then
        local status
        status=$(docker inspect registry --format='{{.State.Status}}')

        if [[ "$status" == "running" ]]; then
            print_success "Registry container is already running"
            return 0
        else
            print_info "Registry container exists but is not running"
            return 1
        fi
    else
        print_info "Registry container does not exist"
        return 1
    fi
}

print_summary() {
    echo ""
    echo -e "${BLUE}===============================================================${NC}"
    echo -e "${GREEN}  REGISTRY READY${NC}"
    echo -e "${BLUE}===============================================================${NC}"
    echo ""
    echo "  Registry URL:  http://${REGISTRY_URL}"
    echo "  API Endpoint:  http://${REGISTRY_URL}/v2/_catalog"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Build and push images: ./build-images.sh"
    echo "  2. Start all services:    docker-compose -f infra/docker-compose.yml up -d"
    echo "  3. Check health:          ./health-check.sh"
    echo ""
    echo -e "${BLUE}===============================================================${NC}"
}

# =============================================================================
# Main
# =============================================================================

main() {
    print_banner
    check_docker
    check_compose_file

    echo ""

    if check_registry_container; then
        # Container already running, just verify
        wait_for_registry
        verify_registry
    else
        # Start and verify
        start_registry
        wait_for_registry
        verify_registry
    fi

    print_summary
}

main "$@"
