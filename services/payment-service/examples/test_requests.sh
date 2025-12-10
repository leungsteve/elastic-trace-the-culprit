#!/bin/bash
# Example API requests for Payment Service
# From Commit to Culprit Workshop

BASE_URL="http://localhost:8082"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Payment Service API Examples${NC}"
echo "================================"
echo ""

# Health check
echo -e "${YELLOW}1. Health Check${NC}"
echo "GET ${BASE_URL}/health"
curl -s "${BASE_URL}/health" | jq .
echo ""
echo ""

# Readiness check
echo -e "${YELLOW}2. Readiness Check${NC}"
echo "GET ${BASE_URL}/ready"
curl -s "${BASE_URL}/ready" | jq .
echo ""
echo ""

# Process a payment (credit card)
echo -e "${YELLOW}3. Process Payment - Credit Card${NC}"
echo "POST ${BASE_URL}/api/payments"
PAYMENT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order-example-001",
    "amount": 47.50,
    "currency": "USD",
    "payment_method": "credit_card",
    "customer_id": "customer-123"
  }')

echo "$PAYMENT_RESPONSE" | jq .

# Extract payment_id for next request
PAYMENT_ID=$(echo "$PAYMENT_RESPONSE" | jq -r '.payment_id // empty')
echo ""
echo ""

# Get payment by ID (if payment succeeded)
if [ -n "$PAYMENT_ID" ] && [ "$PAYMENT_ID" != "null" ]; then
    echo -e "${YELLOW}4. Get Payment by ID${NC}"
    echo "GET ${BASE_URL}/api/payments/${PAYMENT_ID}"
    curl -s "${BASE_URL}/api/payments/${PAYMENT_ID}" | jq .
    echo ""
    echo ""
fi

# Process payment - PayPal
echo -e "${YELLOW}5. Process Payment - PayPal${NC}"
echo "POST ${BASE_URL}/api/payments"
curl -s -X POST "${BASE_URL}/api/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order-example-002",
    "amount": 125.00,
    "currency": "USD",
    "payment_method": "paypal",
    "customer_id": "customer-456"
  }' | jq .
echo ""
echo ""

# Process payment - Bank Transfer
echo -e "${YELLOW}6. Process Payment - Bank Transfer${NC}"
echo "POST ${BASE_URL}/api/payments"
curl -s -X POST "${BASE_URL}/api/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order-example-003",
    "amount": 299.99,
    "currency": "USD",
    "payment_method": "bank_transfer",
    "customer_id": "customer-789"
  }' | jq .
echo ""
echo ""

# Invalid payment (negative amount)
echo -e "${YELLOW}7. Invalid Payment - Negative Amount (Should Fail)${NC}"
echo "POST ${BASE_URL}/api/payments"
curl -s -X POST "${BASE_URL}/api/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order-invalid-001",
    "amount": -50.00,
    "currency": "USD",
    "payment_method": "credit_card",
    "customer_id": "customer-999"
  }' | jq .
echo ""
echo ""

# Get non-existent payment
echo -e "${YELLOW}8. Get Non-Existent Payment (Should Return 404)${NC}"
echo "GET ${BASE_URL}/api/payments/00000000-0000-0000-0000-000000000000"
curl -s "${BASE_URL}/api/payments/00000000-0000-0000-0000-000000000000" | jq .
echo ""
echo ""

echo -e "${GREEN}API Examples Complete!${NC}"
echo ""
echo -e "View API documentation at: ${BLUE}${BASE_URL}/api/docs${NC}"
