#!/usr/bin/env bash
# =============================================================================
# rollback.sh - Manual Rollback Script
# =============================================================================
# From Commit to Culprit - Elastic Observability Workshop
#
# Manually rolls back a service to v1.0 (good version).
# This is a convenience wrapper around deploy.sh for quick rollbacks.
#
# Usage: ./rollback.sh <service-name>
# Example: ./rollback.sh order-service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "Usage: $0 <service-name>"
    echo ""
    echo "Rolls back a service to v1.0 (good version)"
    echo ""
    echo "Services:"
    echo "  order-service      Java Spring Boot order processing"
    echo "  inventory-service  Python FastAPI inventory management"
    echo "  payment-service    Python FastAPI payment processing"
    echo ""
    echo "Example:"
    echo "  $0 order-service"
    exit 1
}

if [[ $# -ne 1 ]]; then
    usage
fi

service=$1

echo -e "${YELLOW}"
echo "==============================================================="
echo "  ROLLBACK INITIATED"
echo "==============================================================="
echo -e "${NC}"
echo "  Service: ${service}"
echo "  Target:  v1.0 (good version)"
echo ""

# Use deploy.sh to perform the rollback
"${SCRIPT_DIR}/deploy.sh" "$service" "v1.0"

echo -e "${GREEN}"
echo "==============================================================="
echo "  ROLLBACK COMPLETE"
echo "==============================================================="
echo -e "${NC}"
