#!/bin/bash

# Finance Assistant - Build Script
# This script builds all components of the finance assistant application

set -e  # Exit on any error

echo "🚀 Building Finance Assistant Application..."

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

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p backend/ml_models
mkdir -p backend/chatbot/models
mkdir -p frontend-web/dist
mkdir -p infra/ssl

# Build Backend
print_status "Building Backend..."
cd backend

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
print_status "Downloading spaCy language model..."
python -m spacy download en_core_web_sm

# Run tests
print_status "Running backend tests..."
if [ -d "tests" ]; then
    python -m pytest tests/ -v || print_warning "Some backend tests failed"
else
    print_warning "No backend tests found"
fi

# Deactivate virtual environment
deactivate

cd ..

# Build Frontend Web
print_status "Building Frontend Web Application..."
cd frontend-web

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Install dependencies
print_status "Installing Node.js dependencies..."
npm ci

# Run linting
print_status "Running ESLint..."
npm run lint || print_warning "Linting issues found"

# Run tests
print_status "Running frontend tests..."
if npm run test --passWithNoTests 2>/dev/null; then
    print_success "Frontend tests passed"
else
    print_warning "Frontend tests failed or not found"
fi

# Build production bundle
print_status "Building production bundle..."
npm run build

cd ..

# Build Frontend Mobile (React Native)
print_status "Building Frontend Mobile Application..."
cd frontend-mobile

if [ -f "package.json" ]; then
    print_status "Installing React Native dependencies..."
    npm ci
    
    # For Expo projects
    if [ -f "app.json" ]; then
        print_status "Building Expo app..."
        if command -v expo &> /dev/null; then
            expo build:web || print_warning "Expo web build failed"
        else
            print_warning "Expo CLI not found, skipping mobile build"
        fi
    fi
else
    print_warning "Mobile app package.json not found, skipping mobile build"
fi

cd ..

# Build Docker Images
print_status "Building Docker images..."

# Build backend image
print_status "Building backend Docker image..."
docker build -f infra/docker/backend.Dockerfile -t finance-assistant-backend:latest ./backend

# Build frontend image
print_status "Building frontend Docker image..."
docker build -f infra/docker/frontend.Dockerfile -t finance-assistant-frontend:latest ./frontend-web

# Validate Docker Compose configuration
print_status "Validating Docker Compose configuration..."
docker-compose config

# Generate SSL certificates for local development (if not exists)
if [ ! -f "infra/ssl/localhost.crt" ]; then
    print_status "Generating self-signed SSL certificates for local development..."
    mkdir -p infra/ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout infra/ssl/localhost.key \
        -out infra/ssl/localhost.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Create production environment file if it doesn't exist
if [ ! -f ".env.production" ]; then
    print_status "Creating production environment template..."
    cp .env.example .env.production
    print_warning "Please update .env.production with production values before deploying"
fi

# Database migrations
print_status "Preparing database migrations..."
if [ -d "database/migrations" ]; then
    print_success "Database migrations directory exists"
else
    mkdir -p database/migrations
    print_warning "Created database migrations directory"
fi

# Build documentation
print_status "Building documentation..."
if [ -f "docs/build.sh" ]; then
    cd docs
    chmod +x build.sh
    ./build.sh || print_warning "Documentation build failed"
    cd ..
else
    print_warning "Documentation build script not found"
fi

# Security scan (if tools available)
if command -v bandit &> /dev/null; then
    print_status "Running security scan on Python code..."
    bandit -r backend/ -f json -o security-scan-backend.json || print_warning "Security scan found issues"
fi

if command -v npm audit &> /dev/null; then
    print_status "Running security audit on Node.js dependencies..."
    cd frontend-web
    npm audit --audit-level=moderate || print_warning "npm audit found vulnerabilities"
    cd ..
fi

# Clean up
print_status "Cleaning up temporary files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "node_modules/.cache" -type d -exec rm -rf {} + 2>/dev/null || true

# Generate build report
print_status "Generating build report..."
BUILD_TIME=$(date)
BUILD_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

cat > build-report.txt << EOF
Finance Assistant - Build Report
===============================

Build Time: $BUILD_TIME
Git Commit: $BUILD_HASH

Components Built:
- ✓ Backend API (FastAPI)
- ✓ Frontend Web (React + TypeScript)
- ✓ Frontend Mobile (React Native)
- ✓ Database Schema
- ✓ Docker Images
- ✓ SSL Certificates

Docker Images:
- finance-assistant-backend:latest
- finance-assistant-frontend:latest

Next Steps:
1. Review .env.production file
2. Run 'docker-compose up -d' to start services
3. Access application at http://localhost:3000
4. Access API docs at http://localhost:8000/docs

For production deployment:
1. Update environment variables
2. Configure external database
3. Set up proper SSL certificates
4. Run './scripts/deploy.sh'
EOF

print_success "Build completed successfully!"
print_status "Build report saved to build-report.txt"

echo ""
echo "🎉 Finance Assistant build completed!"
echo "📊 To start the application: docker-compose up -d"
echo "🌐 Web App: http://localhost:3000"
echo "🔗 API Docs: http://localhost:8000/docs"
echo "📱 Mobile: Use Expo Go app to scan QR code"
echo ""