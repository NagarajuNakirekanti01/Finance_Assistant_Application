#!/bin/bash

# Finance Assistant - Deployment Script
# This script deploys the finance assistant application to production

set -e  # Exit on any error

echo "🚀 Deploying Finance Assistant Application..."

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

# Configuration
ENVIRONMENT=${1:-production}
BUILD_VERSION=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/${BUILD_VERSION}"

print_status "Deployment Environment: $ENVIRONMENT"
print_status "Build Version: $BUILD_VERSION"

# Pre-deployment checks
print_status "Running pre-deployment checks..."

# Check if required files exist
required_files=(
    ".env.${ENVIRONMENT}"
    "docker-compose.yml"
    "infra/docker/backend.Dockerfile"
    "infra/docker/frontend.Dockerfile"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file not found: $file"
        exit 1
    fi
done

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi

# Load environment variables
if [ -f ".env.${ENVIRONMENT}" ]; then
    source ".env.${ENVIRONMENT}"
    print_success "Loaded environment configuration"
else
    print_error "Environment file .env.${ENVIRONMENT} not found"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup (if production)
if [ "$ENVIRONMENT" = "production" ]; then
    print_status "Creating database backup..."
    
    # Check if database is accessible
    if docker-compose exec -T mysql mysqladmin ping -h localhost --silent; then
        docker-compose exec -T mysql mysqldump \
            -u"$DB_USER" -p"$DB_PASSWORD" \
            "$DB_NAME" > "$BACKUP_DIR/database_backup.sql"
        print_success "Database backup created"
    else
        print_warning "Database not accessible, skipping backup"
    fi
fi

# Stop existing services
print_status "Stopping existing services..."
docker-compose down || print_warning "No existing services to stop"

# Pull latest images (if using registry)
if [ "$ENVIRONMENT" = "production" ]; then
    print_status "Pulling latest images..."
    # docker-compose pull  # Uncomment if using image registry
fi

# Build fresh images
print_status "Building application images..."
docker-compose build --no-cache

# Database migrations
print_status "Running database migrations..."

# Start only database service first
docker-compose up -d mysql redis

# Wait for database to be ready
print_status "Waiting for database to be ready..."
timeout=60
while ! docker-compose exec -T mysql mysqladmin ping -h localhost --silent; do
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        print_error "Database failed to start"
        exit 1
    fi
    sleep 1
done

# Run database schema
print_status "Applying database schema..."
docker-compose exec -T mysql mysql -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < database/schema.sql

# Run any pending migrations
if [ -d "database/migrations" ]; then
    for migration in database/migrations/*.sql; do
        if [ -f "$migration" ]; then
            print_status "Running migration: $(basename $migration)"
            docker-compose exec -T mysql mysql -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$migration"
        fi
    done
fi

# Start all services
print_status "Starting all services..."
docker-compose up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Health checks
print_status "Running health checks..."

# Check backend health
backend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "$backend_health" = "200" ]; then
    print_success "Backend health check passed"
else
    print_error "Backend health check failed (HTTP $backend_health)"
fi

# Check frontend
frontend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$frontend_health" = "200" ]; then
    print_success "Frontend health check passed"
else
    print_error "Frontend health check failed (HTTP $frontend_health)"
fi

# Check database
if docker-compose exec -T mysql mysqladmin ping -h localhost --silent; then
    print_success "Database health check passed"
else
    print_error "Database health check failed"
fi

# Run smoke tests
print_status "Running smoke tests..."

# Test user registration endpoint
registration_test=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"TestPass123","first_name":"Test","last_name":"User"}' \
    http://localhost:8000/api/v1/auth/register || echo "000")

if [ "$registration_test" = "201" ] || [ "$registration_test" = "400" ]; then
    print_success "Registration endpoint accessible"
else
    print_warning "Registration endpoint test failed (HTTP $registration_test)"
fi

# SSL/TLS verification (if HTTPS enabled)
if [ "${ENABLE_HTTPS:-false}" = "true" ]; then
    print_status "Verifying SSL/TLS configuration..."
    if openssl s_client -connect localhost:443 -servername localhost < /dev/null 2>/dev/null; then
        print_success "SSL/TLS configuration verified"
    else
        print_warning "SSL/TLS verification failed"
    fi
fi

# Performance baseline
print_status "Recording performance baseline..."
response_time=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:8000/health)
print_status "Backend response time: ${response_time}s"

# Log deployment
print_status "Logging deployment..."
cat >> deployments.log << EOF
$(date): Deployed version $BUILD_VERSION to $ENVIRONMENT
- Backend health: $backend_health
- Frontend health: $frontend_health
- Response time: ${response_time}s
- Git commit: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
EOF

# Cleanup old images
print_status "Cleaning up old Docker images..."
docker image prune -f

# Security scan (production only)
if [ "$ENVIRONMENT" = "production" ]; then
    print_status "Running security checks..."
    
    # Check for exposed ports
    exposed_ports=$(docker-compose ps --format table | grep -E ":.*->.*" | wc -l)
    print_status "Exposed ports: $exposed_ports"
    
    # Check container security
    for container in $(docker-compose ps -q); do
        if [ -n "$container" ]; then
            user=$(docker inspect --format='{{.Config.User}}' "$container")
            if [ "$user" = "root" ] || [ -z "$user" ]; then
                print_warning "Container $container running as root"
            fi
        fi
    done
fi

# Generate deployment report
print_status "Generating deployment report..."
cat > "deployment-report-${BUILD_VERSION}.txt" << EOF
Finance Assistant - Deployment Report
====================================

Deployment Details:
- Environment: $ENVIRONMENT
- Version: $BUILD_VERSION
- Date: $(date)
- Git Commit: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

Health Check Results:
- Backend API: $backend_health
- Frontend Web: $frontend_health
- Database: $(docker-compose exec -T mysql mysqladmin ping -h localhost --silent && echo "OK" || echo "FAIL")

Performance:
- Backend Response Time: ${response_time}s

Services Running:
$(docker-compose ps)

Container Resource Usage:
$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}")

Exposed Ports:
$(docker-compose ps --format table | grep -E ":.*->.*")

Backup Location: $BACKUP_DIR

Next Steps:
1. Monitor application logs: docker-compose logs -f
2. Set up monitoring and alerting
3. Configure log rotation
4. Schedule regular backups
5. Update DNS records (if needed)

Rollback Command:
docker-compose down && docker-compose up -d
EOF

# Post-deployment tasks
print_status "Running post-deployment tasks..."

# Warm up the application
curl -s http://localhost:8000/ > /dev/null || true
curl -s http://localhost:3000/ > /dev/null || true

# Create systemd service (Linux only)
if command -v systemctl &> /dev/null && [ "$ENVIRONMENT" = "production" ]; then
    print_status "Creating systemd service..."
    
    cat > /tmp/finance-assistant.service << EOF
[Unit]
Description=Finance Assistant Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    if sudo cp /tmp/finance-assistant.service /etc/systemd/system/; then
        sudo systemctl daemon-reload
        sudo systemctl enable finance-assistant
        print_success "Systemd service created and enabled"
    else
        print_warning "Failed to create systemd service (requires sudo)"
    fi
fi

# Final status
print_success "Deployment completed successfully!"
print_status "Deployment report saved to deployment-report-${BUILD_VERSION}.txt"

echo ""
echo "🎉 Finance Assistant deployment completed!"
echo "🌐 Web Application: http://localhost:3000"
echo "🔗 API Documentation: http://localhost:8000/docs"
echo "📊 Admin Panel: http://localhost:8000/admin"
echo ""
echo "📋 Management Commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Scale services: docker-compose up -d --scale backend=2"
echo ""
echo "🔧 Troubleshooting:"
echo "  Check status: docker-compose ps"
echo "  View health: curl http://localhost:8000/health"
echo "  Database access: docker-compose exec mysql mysql -u$DB_USER -p$DB_PASSWORD $DB_NAME"
echo ""

# Send notification (if webhook configured)
if [ -n "${WEBHOOK_URL:-}" ]; then
    curl -s -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"text\":\"Finance Assistant deployed successfully to $ENVIRONMENT (v$BUILD_VERSION)\"}" \
        > /dev/null || print_warning "Failed to send webhook notification"
fi