# Finance Assistant - Complete Full-Stack Application

A comprehensive personal finance management platform with AI-powered insights, budget prediction, and intelligent chatbot assistance.

##  Architecture

- **Backend**: FastAPI + SQLAlchemy + MySQL
- **Frontend Web**: React + TypeScript + Vite + TailwindCSS  
- **Frontend Mobile**: React Native
- **Database**: MySQL 8.0
- **AI/ML**: Budget prediction (scikit-learn) + NLP Chatbot (spaCy)
- **Authentication**: JWT + MFA + Role-Based Access Control
- **Infrastructure**: Docker + Kubernetes + Terraform

##  Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.9+
- MySQL 8.0

### Development Setup

1. **Clone and setup environment**
```bash
cp .env.example .env
# Update .env with your configurations
```

2. **Start with Docker**
```bash
docker-compose up -d
```

3. **Manual setup (alternative)**
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend Web
cd frontend-web
npm install
npm run dev

# Frontend Mobile
cd frontend-mobile
npm install
npx expo start
```

## 📱 Features

### Core Functionality
- ✅ Multi-factor Authentication (JWT + TOTP)
- ✅ Bank Account Integration (mocked APIs)
- ✅ Smart Expense Categorization
- ✅ AI Budget Prediction Engine
- ✅ What-if Savings Scenarios
- ✅ Financial Health Reports
- ✅ Intelligent Chatbot with Charts
- ✅ PDF/Excel Export
- ✅ GDPR Compliance
- ✅ End-to-end Encryption

### Security & Compliance
- 🔐 AES-256 encryption at rest
- 🔐 TLS 1.3 encryption in transit
- 🔐 GDPR-aligned data handling
- 🔐 Role-based access control
- 🔐 Audit logging

## 🧪 Testing

```bash
# Backend tests
cd backend && python -m pytest tests/

# Frontend tests  
cd frontend-web && npm test

# Integration tests
./scripts/test.sh
```

## 🚢 Deployment

```bash
# Build all services
./scripts/build.sh

# Deploy to production
./scripts/deploy.sh
```

## 📚 Documentation

- [Software Requirements Specification](docs/SRS.pdf)
- [Architecture Guide](docs/architecture.md)
- [API Documentation](docs/api-docs/)
- [User Guide](docs/user-guide.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.