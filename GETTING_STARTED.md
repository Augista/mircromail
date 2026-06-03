# MicroMail - Getting Started Guide

Welcome to MicroMail! This guide will help you set up and run the application locally.

## Quick Start (5 minutes)

### Step 1: Clone and Install

```bash
# Install frontend dependencies
pnpm install

# Copy environment file
cp .env.example .env.local
```

### Step 2: Run Frontend

```bash
pnpm dev
```

Visit `http://localhost:3000` and you'll see the login page!

### Step 3: Run Backend Services (Optional)

If you want to test the full API integration:

```bash
# Make sure Docker is running
docker-compose up -d
```

This starts:
- PostgreSQL databases
- RabbitMQ message broker
- API Gateway
- All microservices

## Detailed Setup

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend services)
- **Docker & Docker Compose** (for running services)
- **pnpm** (or npm/yarn)

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd /path/to/micromail
   pnpm install
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env.local
   ```

3. **Start development server:**
   ```bash
   pnpm dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - API Gateway: http://localhost:8000 (when services running)

### Backend Services Setup

#### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

This will start:
- **API Gateway** at http://localhost:8000
- **Auth Service** at http://localhost:8001
- **Composer Service** at http://localhost:8002
- **Storage Service** at http://localhost:8003
- **Delivery Service** at http://localhost:8004
- **RabbitMQ** at http://localhost:5672 (amqp)
- **RabbitMQ Management** at http://localhost:15672 (guest/guest)
- **PostgreSQL** databases at localhost:5432, 5433, 5434

#### Option 2: Manual Setup

1. **Install Python dependencies:**
   ```bash
   cd services
   pip install -r requirements.txt
   cd ..
   ```

2. **Start RabbitMQ** (requires Docker):
   ```bash
   docker run -d --name rabbitmq \
     -p 5672:5672 \
     -p 15672:15672 \
     rabbitmq:3.12-management-alpine
   ```

3. **Start each service** in separate terminals:
   ```bash
   # Terminal 1: Auth Service
   cd services/auth && python main.py

   # Terminal 2: Gateway
   cd services/gateway && python main.py

   # Terminal 3: Composer
   cd services/composer && python main.py

   # Terminal 4: Storage
   cd services/storage && python main.py

   # Terminal 5: Delivery
   cd services/delivery && python main.py
   ```

## Testing the Application

### Login Flow

1. Go to http://localhost:3000
2. Click "Create one" to register a new account
3. Fill in: Name, Email, Password
4. Click "Create account"
5. You'll be redirected to the inbox

### Available Features (Demo)

- **Authentication**: Register and login (frontend only, backend API ready)
- **Inbox**: View mock emails with search functionality
- **Folders**: Switch between Inbox, Sent, Drafts, Trash
- **Email Details**: Click email to see full content
- **Compose**: Click "Compose" button to open email composer (frontend UI ready)
- **Search**: Search emails by subject, sender, or content

### API Testing

Once services are running, test the API directly:

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# Use returned token for authenticated requests
curl -X GET http://localhost:8000/api/inbox \
  -H "Authorization: Bearer <your_token_here>"
```

## Project Structure

```
micromail/
├── app/                          # Next.js frontend
│   ├── (auth)/                  # Auth pages (login, register)
│   ├── (mail)/                  # Mail interface
│   └── layout.tsx
├── components/
│   ├── mail/                    # Mail-specific components
│   └── ui/                      # shadcn/ui components
├── lib/
│   └── api.ts                   # API client library
├── services/                     # Backend microservices
│   ├── gateway/                 # API Gateway (routes requests)
│   ├── auth/                    # Authentication service
│   ├── composer/                # Draft management
│   ├── storage/                 # Email storage (CQRS)
│   ├── delivery/                # SMTP email sending
│   └── requirements.txt
├── docker-compose.yml           # Orchestration
├── .env.example                 # Environment template
├── README.md                     # Full documentation
├── GETTING_STARTED.md          # This file
└── ARCHITECTURE.md             # Technical architecture
```

## Frontend Development

### Available Scripts

```bash
# Start development server with hot reload
pnpm dev

# Build for production
pnpm build

# Run production build locally
pnpm start

# Run linter
pnpm lint

# Type check
pnpm type-check
```

### File Structure

- **app/(auth)/** - Authentication pages
  - `login/page.tsx` - Login form
  - `register/page.tsx` - Registration form

- **app/(mail)/** - Mail interface
  - `layout.tsx` - Mail layout with sidebar and header
  - `inbox/page.tsx` - Inbox view with email list
  - `sent/page.tsx` - Sent emails
  - `drafts/page.tsx` - Draft emails
  - `trash/page.tsx` - Deleted emails

- **components/mail/** - Mail components
  - `mail-sidebar.tsx` - Folder navigation
  - `mail-header.tsx` - Top bar with search and user menu
  - `mail-list-view.tsx` - Email list
  - `mail-detail-view.tsx` - Email details
  - `mail-composer.tsx` - Compose email dialog

## Backend Development

### Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| API Gateway | 8000 | Single entry point for frontend |
| Auth Service | 8001 | User authentication |
| Composer Service | 8002 | Draft management |
| Storage Service | 8003 | Email storage |
| Delivery Service | 8004 | Email sending |
| RabbitMQ | 5672 | Message queue |
| RabbitMQ UI | 15672 | Management console |

### Database Ports

| Database | Port | User | Password |
|----------|------|------|----------|
| auth_db | 5432 | auth_user | auth_password |
| composer_db | 5433 | composer_user | composer_password |
| storage_db | 5434 | storage_user | storage_password |

## Common Tasks

### View RabbitMQ Messages

1. Open http://localhost:15672
2. Username: `guest`
3. Password: `guest`
4. Go to **Queues** tab
5. Click on queue to see messages

### Access PostgreSQL Directly

```bash
# Auth database
psql -h localhost -p 5432 -U auth_user -d auth_db

# Composer database
psql -h localhost -p 5433 -U composer_user -d composer_db

# Storage database
psql -h localhost -p 5434 -U storage_user -d storage_db
```

### Check Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f auth_service

# Follow logs
docker-compose logs --tail=100 -f
```

### Reset Everything

```bash
# Stop services
docker-compose down

# Remove volumes (clears all data)
docker-compose down -v

# Restart
docker-compose up -d
```

## Troubleshooting

### Services Not Starting

**Error: "Cannot connect to Docker daemon"**
- Make sure Docker is running: `docker ps`
- On Mac/Windows, start Docker Desktop

**Error: "Port already in use"**
- Change port in `docker-compose.yml` or stop conflicting service

### Frontend Issues

**Login/Register not working**
- Check that API Gateway is running: `curl http://localhost:8000/health`
- Check browser console for errors (F12)
- Ensure `NEXT_PUBLIC_API_URL` in `.env.local` matches your setup

**Emails not loading**
- Check API Gateway logs: `docker-compose logs api_gateway`
- Verify Storage Service is running

### Database Issues

**Can't connect to PostgreSQL**
```bash
# Check if container is running
docker-compose ps

# Check logs
docker-compose logs postgres_service

# Restart service
docker-compose restart auth_db
```

## Next Steps

1. **Understand the Architecture**: Read [ARCHITECTURE.md](./ARCHITECTURE.md)
2. **Explore the API**: Check [services/API.md](./services/API.md)
3. **Connect a Real Database**: Replace mock databases with PostgreSQL
4. **Add SMTP Config**: Configure real email sending
5. **Deploy**: Set up production environment

## Resources

- **Next.js**: https://nextjs.org/docs
- **FastAPI**: https://fastapi.tiangolo.com
- **RabbitMQ**: https://www.rabbitmq.com/
- **shadcn/ui**: https://ui.shadcn.com
- **Docker**: https://docs.docker.com

## Support

- **Issues**: Open an issue on GitHub
- **Questions**: Check the [README.md](./README.md)
- **Architecture**: See [ARCHITECTURE.md](./ARCHITECTURE.md)

---

**Happy coding! 🚀**

For more detailed information, see the full README.md or check the API documentation.
