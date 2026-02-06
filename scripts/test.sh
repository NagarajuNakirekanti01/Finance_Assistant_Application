#!/bin/bash

# Finance Assistant - Test Script
# Comprehensive testing suite for all application components

set -e  # Exit on any error

echo "🧪 Running Finance Assistant Test Suite..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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
TEST_START_TIME=$(date +%s)
TEST_RESULTS_DIR="test-results/$(date +%Y%m%d_%H%M%S)"
BACKEND_TESTS_PASSED=0
FRONTEND_TESTS_PASSED=0
INTEGRATION_TESTS_PASSED=0
TOTAL_TESTS=0

# Create test results directory
mkdir -p "$TEST_RESULTS_DIR"

# Function to record test result
record_test() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    echo "$test_name: $result - $details" >> "$TEST_RESULTS_DIR/test_results.txt"
    
    if [ "$result" = "PASS" ]; then
        case "$test_name" in
            *backend*) BACKEND_TESTS_PASSED=$((BACKEND_TESTS_PASSED + 1)) ;;
            *frontend*) FRONTEND_TESTS_PASSED=$((FRONTEND_TESTS_PASSED + 1)) ;;
            *integration*) INTEGRATION_TESTS_PASSED=$((INTEGRATION_TESTS_PASSED + 1)) ;;
        esac
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# Backend Tests
print_status "Running Backend Tests..."

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment for testing..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
print_status "Installing test dependencies..."
pip install pytest pytest-asyncio pytest-cov httpx

# Unit Tests
print_status "Running backend unit tests..."
if python -m pytest tests/unit/ -v --cov=app --cov-report=html:"../$TEST_RESULTS_DIR/backend_coverage" --cov-report=term; then
    record_test "backend_unit_tests" "PASS" "All unit tests passed"
    print_success "Backend unit tests passed"
else
    record_test "backend_unit_tests" "FAIL" "Some unit tests failed"
    print_error "Backend unit tests failed"
fi

# Integration Tests
print_status "Running backend integration tests..."
if python -m pytest tests/integration/ -v; then
    record_test "backend_integration_tests" "PASS" "All integration tests passed"
    print_success "Backend integration tests passed"
else
    record_test "backend_integration_tests" "FAIL" "Some integration tests failed"
    print_warning "Backend integration tests failed"
fi

# Security Tests
print_status "Running security tests..."
if command -v bandit &> /dev/null; then
    if bandit -r app/ -f json -o "../$TEST_RESULTS_DIR/security_report.json"; then
        record_test "backend_security" "PASS" "No security issues found"
        print_success "Security scan passed"
    else
        record_test "backend_security" "FAIL" "Security issues found"
        print_warning "Security scan found issues"
    fi
else
    record_test "backend_security" "SKIP" "Bandit not installed"
    print_warning "Bandit not available, skipping security tests"
fi

# Code Quality Tests
print_status "Running code quality checks..."
if command -v flake8 &> /dev/null; then
    if flake8 app/ --output-file="../$TEST_RESULTS_DIR/flake8_report.txt"; then
        record_test "backend_code_quality" "PASS" "Code quality checks passed"
        print_success "Code quality checks passed"
    else
        record_test "backend_code_quality" "FAIL" "Code quality issues found"
        print_warning "Code quality issues found"
    fi
else
    print_warning "Flake8 not available, skipping code quality tests"
fi

# Type Checking
print_status "Running type checking..."
if command -v mypy &> /dev/null; then
    if mypy app/ --ignore-missing-imports > "../$TEST_RESULTS_DIR/mypy_report.txt"; then
        record_test "backend_type_checking" "PASS" "Type checking passed"
        print_success "Type checking passed"
    else
        record_test "backend_type_checking" "FAIL" "Type checking issues found"
        print_warning "Type checking issues found"
    fi
fi

deactivate
cd ..

# Frontend Tests
print_status "Running Frontend Tests..."

cd frontend-web

# Install dependencies if not present
if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm ci
fi

# Unit Tests
print_status "Running frontend unit tests..."
if npm test -- --coverage --watchAll=false --coverageDirectory="../$TEST_RESULTS_DIR/frontend_coverage"; then
    record_test "frontend_unit_tests" "PASS" "All frontend unit tests passed"
    print_success "Frontend unit tests passed"
else
    record_test "frontend_unit_tests" "FAIL" "Some frontend unit tests failed"
    print_warning "Frontend unit tests failed"
fi

# Linting
print_status "Running ESLint..."
if npm run lint > "../$TEST_RESULTS_DIR/eslint_report.txt" 2>&1; then
    record_test "frontend_linting" "PASS" "No linting errors"
    print_success "Linting passed"
else
    record_test "frontend_linting" "FAIL" "Linting errors found"
    print_warning "Linting errors found"
fi

# Type Checking
print_status "Running TypeScript type checking..."
if npx tsc --noEmit > "../$TEST_RESULTS_DIR/typescript_report.txt" 2>&1; then
    record_test "frontend_type_checking" "PASS" "No type errors"
    print_success "TypeScript type checking passed"
else
    record_test "frontend_type_checking" "FAIL" "Type errors found"
    print_warning "TypeScript type errors found"
fi

# Build Test
print_status "Testing production build..."
if npm run build > "../$TEST_RESULTS_DIR/build_report.txt" 2>&1; then
    record_test "frontend_build" "PASS" "Production build successful"
    print_success "Production build test passed"
else
    record_test "frontend_build" "FAIL" "Production build failed"
    print_error "Production build test failed"
fi

# Bundle Analysis
print_status "Analyzing bundle size..."
if [ -d "dist" ]; then
    bundle_size=$(du -sh dist | cut -f1)
    echo "Bundle size: $bundle_size" > "../$TEST_RESULTS_DIR/bundle_analysis.txt"
    record_test "frontend_bundle_size" "INFO" "Bundle size: $bundle_size"
    print_status "Bundle size: $bundle_size"
fi

cd ..

# Database Tests
print_status "Running Database Tests..."

# Check if Docker is available for database tests
if command -v docker &> /dev/null; then
    # Start test database
    print_status "Starting test database..."
    docker run -d --name test-mysql \
        -e MYSQL_ROOT_PASSWORD=testpass \
        -e MYSQL_DATABASE=finance_assistant_test \
        -p 3307:3306 \
        mysql:8.0
    
    # Wait for database to be ready
    sleep 30
    
    # Test database connection
    if docker exec test-mysql mysqladmin ping -h localhost --silent; then
        record_test "database_connection" "PASS" "Database connection successful"
        print_success "Database connection test passed"
    else
        record_test "database_connection" "FAIL" "Database connection failed"
        print_error "Database connection test failed"
    fi
    
    # Test schema creation
    if docker exec -i test-mysql mysql -uroot -ptestpass finance_assistant_test < database/schema.sql; then
        record_test "database_schema" "PASS" "Schema creation successful"
        print_success "Database schema test passed"
    else
        record_test "database_schema" "FAIL" "Schema creation failed"
        print_error "Database schema test failed"
    fi
    
    # Cleanup test database
    docker stop test-mysql
    docker rm test-mysql
    
else
    print_warning "Docker not available, skipping database tests"
fi

# Integration Tests (Full Stack)
print_status "Running Integration Tests..."

# Start services for integration testing
if command -v docker-compose &> /dev/null; then
    print_status "Starting services for integration testing..."
    
    # Use test environment
    export COMPOSE_FILE=docker-compose.yml
    export COMPOSE_PROJECT_NAME=finance_assistant_test
    
    docker-compose up -d
    
    # Wait for services to be ready
    sleep 60
    
    # API Integration Tests
    print_status "Running API integration tests..."
    
    # Test health endpoint
    health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    if [ "$health_response" = "200" ]; then
        record_test "integration_api_health" "PASS" "Health endpoint responsive"
        print_success "API health test passed"
    else
        record_test "integration_api_health" "FAIL" "Health endpoint not responsive"
        print_error "API health test failed"
    fi
    
    # Test user registration
    registration_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"TestPass123","first_name":"Test","last_name":"User"}' \
        http://localhost:8000/api/v1/auth/register)
    
    if [ "$registration_response" = "201" ]; then
        record_test "integration_user_registration" "PASS" "User registration successful"
        print_success "User registration test passed"
    else
        record_test "integration_user_registration" "FAIL" "User registration failed"
        print_warning "User registration test failed (HTTP $registration_response)"
    fi
    
    # Test frontend accessibility
    frontend_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
    if [ "$frontend_response" = "200" ]; then
        record_test "integration_frontend_access" "PASS" "Frontend accessible"
        print_success "Frontend accessibility test passed"
    else
        record_test "integration_frontend_access" "FAIL" "Frontend not accessible"
        print_error "Frontend accessibility test failed"
    fi
    
    # Performance Tests
    print_status "Running performance tests..."
    
    # API response time test
    api_response_time=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:8000/health)
    if (( $(echo "$api_response_time < 1.0" | bc -l) )); then
        record_test "performance_api_response" "PASS" "API response time: ${api_response_time}s"
        print_success "API performance test passed"
    else
        record_test "performance_api_response" "FAIL" "API response time: ${api_response_time}s (>1s)"
        print_warning "API performance test failed"
    fi
    
    # Load test (basic)
    print_status "Running basic load test..."
    if command -v ab &> /dev/null; then
        ab -n 100 -c 10 http://localhost:8000/health > "$TEST_RESULTS_DIR/load_test.txt" 2>&1
        record_test "performance_load_test" "PASS" "Load test completed (100 requests, 10 concurrent)"
        print_success "Load test completed"
    else
        print_warning "Apache Bench not available, skipping load test"
    fi
    
    # Cleanup
    docker-compose down
    docker-compose rm -f
    
else
    print_warning "Docker Compose not available, skipping integration tests"
fi

# End-to-End Tests (if Playwright/Cypress available)
print_status "Checking for E2E tests..."

if [ -f "frontend-web/playwright.config.js" ] || [ -f "frontend-web/cypress.json" ]; then
    print_status "Running E2E tests..."
    cd frontend-web
    
    if command -v npx playwright &> /dev/null; then
        npx playwright test > "../$TEST_RESULTS_DIR/e2e_results.txt" 2>&1
        if [ $? -eq 0 ]; then
            record_test "e2e_tests" "PASS" "E2E tests passed"
            print_success "E2E tests passed"
        else
            record_test "e2e_tests" "FAIL" "E2E tests failed"
            print_warning "E2E tests failed"
        fi
    elif command -v npx cypress &> /dev/null; then
        npx cypress run > "../$TEST_RESULTS_DIR/e2e_results.txt" 2>&1
        if [ $? -eq 0 ]; then
            record_test "e2e_tests" "PASS" "E2E tests passed"
            print_success "E2E tests passed"
        else
            record_test "e2e_tests" "FAIL" "E2E tests failed"
            print_warning "E2E tests failed"
        fi
    fi
    
    cd ..
else
    print_status "No E2E test configuration found, skipping"
fi

# Mobile App Tests (if React Native)
if [ -d "frontend-mobile" ] && [ -f "frontend-mobile/package.json" ]; then
    print_status "Running mobile app tests..."
    cd frontend-mobile
    
    if npm test -- --watchAll=false > "../$TEST_RESULTS_DIR/mobile_test_results.txt" 2>&1; then
        record_test "mobile_tests" "PASS" "Mobile tests passed"
        print_success "Mobile tests passed"
    else
        record_test "mobile_tests" "FAIL" "Mobile tests failed"
        print_warning "Mobile tests failed"
    fi
    
    cd ..
fi

# Generate Test Report
TEST_END_TIME=$(date +%s)
TEST_DURATION=$((TEST_END_TIME - TEST_START_TIME))

print_status "Generating comprehensive test report..."

cat > "$TEST_RESULTS_DIR/test_summary.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Finance Assistant - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .pass { color: green; }
        .fail { color: red; }
        .skip { color: orange; }
        .section { margin: 20px 0; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Finance Assistant - Test Report</h1>
        <p><strong>Date:</strong> $(date)</p>
        <p><strong>Duration:</strong> ${TEST_DURATION} seconds</p>
        <p><strong>Total Tests:</strong> $TOTAL_TESTS</p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <ul>
            <li>Backend Tests Passed: $BACKEND_TESTS_PASSED</li>
            <li>Frontend Tests Passed: $FRONTEND_TESTS_PASSED</li>
            <li>Integration Tests Passed: $INTEGRATION_TESTS_PASSED</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Detailed Results</h2>
        <table>
            <tr><th>Test</th><th>Result</th><th>Details</th></tr>
EOF

# Add test results to HTML
while IFS=': ' read -r test_name result_details; do
    IFS=' - ' read -r result details <<< "$result_details"
    css_class="pass"
    if [ "$result" = "FAIL" ]; then css_class="fail"; fi
    if [ "$result" = "SKIP" ]; then css_class="skip"; fi
    
    echo "            <tr><td>$test_name</td><td class=\"$css_class\">$result</td><td>$details</td></tr>" >> "$TEST_RESULTS_DIR/test_summary.html"
done < "$TEST_RESULTS_DIR/test_results.txt"

cat >> "$TEST_RESULTS_DIR/test_summary.html" << EOF
        </table>
    </div>
</body>
</html>
EOF

# Create JSON report for CI/CD integration
cat > "$TEST_RESULTS_DIR/test_results.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "duration": $TEST_DURATION,
    "total_tests": $TOTAL_TESTS,
    "backend_tests_passed": $BACKEND_TESTS_PASSED,
    "frontend_tests_passed": $FRONTEND_TESTS_PASSED,
    "integration_tests_passed": $INTEGRATION_TESTS_PASSED,
    "test_results_dir": "$TEST_RESULTS_DIR",
    "git_commit": "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
}
EOF

# Final Summary
print_success "Test suite completed!"
print_status "Test duration: ${TEST_DURATION} seconds"
print_status "Total tests run: $TOTAL_TESTS"
print_status "Backend tests passed: $BACKEND_TESTS_PASSED"
print_status "Frontend tests passed: $FRONTEND_TESTS_PASSED"
print_status "Integration tests passed: $INTEGRATION_TESTS_PASSED"

echo ""
echo "📊 Test Results:"
echo "📁 Results directory: $TEST_RESULTS_DIR"
echo "📄 HTML Report: $TEST_RESULTS_DIR/test_summary.html"
echo "📄 JSON Report: $TEST_RESULTS_DIR/test_results.json"
echo "📄 Coverage Reports: $TEST_RESULTS_DIR/*_coverage/"
echo ""

# Check if any critical tests failed
critical_failures=$(grep "FAIL" "$TEST_RESULTS_DIR/test_results.txt" | grep -E "(backend_unit|integration_api|database)" | wc -l)

if [ "$critical_failures" -gt 0 ]; then
    print_error "Critical test failures detected! Review test results before deployment."
    exit 1
else
    print_success "All critical tests passed! ✅"
fi

echo "🎉 Testing complete!"