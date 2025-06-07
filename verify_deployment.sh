#!/bin/bash

# ******************** Deployment Verification Script ********************#
# Verify that separate deployment is working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
TEST_QUESTION="What is machine learning?"

echo "🔍 TDS Teaching Assistant - Deployment Verification"
echo "=================================================="

# Test 1: Backend Health Check
print_status "Testing backend health check..."
if curl -f -s "$BACKEND_URL/health" > /dev/null; then
    print_success "Backend health check passed"
    
    # Get health details
    HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health")
    echo "   Status: $(echo $HEALTH_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)"
else
    print_error "Backend health check failed"
    print_error "Make sure backend is running on $BACKEND_URL"
    exit 1
fi

# Test 2: Frontend Health Check
print_status "Testing frontend accessibility..."
if curl -f -s "$FRONTEND_URL" > /dev/null; then
    print_success "Frontend is accessible"
else
    print_error "Frontend is not accessible"
    print_error "Make sure frontend is running on $FRONTEND_URL"
    exit 1
fi

# Test 3: API Functionality
print_status "Testing API functionality..."
API_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"$TEST_QUESTION\"}" \
    -w "HTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$API_RESPONSE" | tail -n1 | cut -d: -f2)
RESPONSE_BODY=$(echo "$API_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    print_success "API functionality test passed"
    
    # Check if response contains expected fields
    if echo "$RESPONSE_BODY" | grep -q '"answer"'; then
        print_success "API response contains answer field"
    else
        print_warning "API response may be malformed"
    fi
else
    print_error "API functionality test failed (HTTP $HTTP_CODE)"
    echo "Response: $RESPONSE_BODY"
fi

# Test 4: CORS Configuration
print_status "Testing CORS configuration..."
CORS_RESPONSE=$(curl -s -X OPTIONS "$BACKEND_URL/api/v1/ask" \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: POST" \
    -w "HTTP_CODE:%{http_code}")

CORS_HTTP_CODE=$(echo "$CORS_RESPONSE" | tail -n1 | cut -d: -f2)

if [ "$CORS_HTTP_CODE" = "200" ] || [ "$CORS_HTTP_CODE" = "204" ]; then
    print_success "CORS configuration is working"
else
    print_error "CORS configuration may have issues"
fi

# Test 5: Frontend-Backend Integration
print_status "Testing frontend-backend integration..."
# This is a basic check - in a real scenario, you might use Selenium or similar
if curl -s "$FRONTEND_URL" | grep -q "TDS\|Teaching\|Assistant"; then
    print_success "Frontend appears to be the correct application"
else
    print_warning "Frontend content verification inconclusive"
fi

# Test 6: Configuration Endpoints
print_status "Testing configuration endpoints..."
if curl -f -s "$BACKEND_URL/api/v1/config" > /dev/null; then
    print_success "Configuration endpoint is accessible"
else
    print_warning "Configuration endpoint may not be working"
fi

# Test 7: Collections Endpoint
print_status "Testing collections endpoint..."
if curl -f -s "$BACKEND_URL/collections" > /dev/null; then
    print_success "Collections endpoint is accessible"
else
    print_warning "Collections endpoint may not be working"
fi

echo ""
echo "🎯 Verification Summary"
echo "======================"

# Performance test
print_status "Running quick performance test..."
START_TIME=$(date +%s%N)
curl -s -X POST "$BACKEND_URL/api/v1/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"Hello\"}" > /dev/null
END_TIME=$(date +%s%N)
RESPONSE_TIME=$((($END_TIME - $START_TIME) / 1000000))

if [ $RESPONSE_TIME -lt 2000 ]; then
    print_success "Response time: ${RESPONSE_TIME}ms (Good)"
elif [ $RESPONSE_TIME -lt 5000 ]; then
    print_warning "Response time: ${RESPONSE_TIME}ms (Acceptable)"
else
    print_error "Response time: ${RESPONSE_TIME}ms (Slow)"
fi

echo ""
print_success "✅ Verification completed!"
echo ""
echo "📍 Service URLs:"
echo "   Backend:  $BACKEND_URL"
echo "   Frontend: $FRONTEND_URL"
echo "   API Docs: $BACKEND_URL/docs"
echo ""
echo "🔗 Test the application:"
echo "   1. Open $FRONTEND_URL in your browser"
echo "   2. Ask a question about the TDS course"
echo "   3. Verify the response is relevant and helpful"
echo ""

# Additional checks
if command -v docker &> /dev/null; then
    print_status "Docker containers:"
    docker ps | grep -E "(tds|teaching)" || echo "   No TDS containers found"
fi

if command -v kubectl &> /dev/null; then
    print_status "Kubernetes pods:"
    kubectl get pods -n tds-assistant 2>/dev/null || echo "   No TDS namespace found"
fi

echo ""
echo "🚀 Your TDS Teaching Assistant is ready for use!"
