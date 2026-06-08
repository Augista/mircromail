# MicroMail - Gmail-Like Webmail Platform

A full-featured webmail platform built with microservices architecture, featuring real-time email management, user authentication, and distributed communication.

## Project Structure

```
├── app/                          # Next.js frontend application
│   ├── (auth)/                  # Authentication pages
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (mail)/                  # Mail interface
│   │   ├── inbox/page.tsx
│   │   ├── sent/page.tsx
│   │   ├── drafts/page.tsx
│   │   └── trash/page.tsx
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/                   # React components
│   ├── mail/
│   │   ├── mail-sidebar.tsx
│   │   ├── mail-header.tsx
│   │   ├── mail-list-view.tsx
│   │   └── mail-detail-view.tsx
│   └── ui/                      # shadcn/ui components
├── lib/
│   └── api.ts                   # API client
├── services/                     # Microservices
│   ├── gateway/                 # API Gateway
│   │   ├── main.py
│   │   └── Dockerfile
│   ├── auth/                    # Authentication Service
│   │   ├── main.py
│   │   └── Dockerfile
│   ├── mail-service/                # Mail Composer Service (placeholder)

├── docker-compose.yml           # Local development setup
├── .env.example                 # Environment variables
└── README.md

```

```
Cara 1: Docker Compose (Recommended)
Ini cara paling mudah — semua service jalan otomatis.

Step 1 — Pastikan Docker Desktop sudah running, lalu dari root project:


docker-compose up --build
Ini akan menyalakan:

auth_db (PostgreSQL :5432)
mail_db (PostgreSQL :5435)
rabbitmq (:5672)
auth_service (:8001)
mail_service (:8004)
api_gateway (:8000)
prometheus + grafana (monitoring)
Migrasi database berjalan otomatis karena Dockerfile sudah diupdate.

Step 2 — Jalankan frontend di terminal terpisah:


npm install
npm run dev
Step 3 — Buka browser:


http://localhost:3000
Cara 2: Local (Tanpa Docker)
Butuh PostgreSQL dan RabbitMQ sudah berjalan di localhost.

Terminal 1 — Auth Service:


cd services/auth-service
# .env sudah ada, tapi JWT_SECRET-nya "super-secret-key"
alembic upgrade head
python main.py
Terminal 2 — Mail Service:


cd services/mail-service
# Buat .env dari .env.example dulu:
copy .env.example .env
# Edit DATABASE_URL dan RABBITMQ_URL di .env itu
alembic upgrade head
python main.py
Terminal 3 — API Gateway:


cd services/api-gateway
# Buat .env baru:
# JWT_SECRET=super-secret-key   ← HARUS sama dengan auth-service!
# AUTH_SERVICE_URL=http://localhost:8001
# MAIL_SERVICE_URL=http://localhost:8004
python main.py
Terminal 4 — Frontend:


# dari root project
npm install
npm run dev
Catatan Penting
Docker Compose	Local
JWT_SECRET	Otomatis sama (your-secret-key-change-in-production)	Harus disamakan manual
Database	Auto-create via docker	PostgreSQL harus sudah jalan
RabbitMQ	Auto via docker	Harus install + jalankan sendiri
Migrasi	Otomatis (Dockerfile diupdate)	Jalankan alembic upgrade head manual
File .env di root sudah benar — NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Architecture

MicroMail uses a microservices architecture with the following components:

### Frontend
- **Next.js 16** with TypeScript
- **shadcn/ui** components
- **Tailwind CSS** styling
- Client-side state management with React Context

### Backend Services

1. **API Gateway** (Port 8000)
   - Routes requests to appropriate microservices
   - Handles authentication and authorization
   - Rate limiting and request logging

2. **Auth Service** (Port 8001)
   - User registration and login
   - JWT token generation and validation
   - Password hashing with bcrypt

3. **Mail Composer Service** (Port 8002)
   - Email draft creation and management
   - Email composition with validation

4. **Mail Storage Service** (Port 8003)
   - Email storage (Inbox, Sent, Trash)
   - Email search and retrieval
   - CQRS pattern for read/write separation

5. **Mail Delivery Service** (Port 8004)
   - SMTP email sending
   - Delivery confirmation
   - Async processing via RabbitMQ

### Infrastructure
- **PostgreSQL** - Database per service pattern
- **RabbitMQ** - Message queue for async communication
- **Docker** - Containerization for all services

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker and Docker Compose (for running services)
- pnpm (or npm/yarn)

### Frontend Setup

1. Install dependencies:
```bash
pnpm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
# Update NEXT_PUBLIC_API_URL if needed
```

3. Run the development server:
```bash
pnpm dev
```

The frontend will be available at `http://localhost:3000`

### Backend Services Setup

1. Install Python dependencies:
```bash
cd services
pip install -r requirements.txt
cd ..
```

2. Set up environment variables:
```bash
cp .env.example .env
# Update with your configuration
```

3. Start all services with Docker Compose:
```bash
docker-compose up -d
```

This will start:
- PostgreSQL databases (ports 5432-5434)
- RabbitMQ (ports 5672, 15672)
- API Gateway (port 8000)
- All microservices (ports 8001-8004)

### Accessing the Application

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## Development Workflow

### Frontend Development

```bash
# Run dev server with hot reload
pnpm dev

# Build for production
pnpm build

# Run production build
pnpm start

# Run linter
pnpm lint
```

### Backend Development

1. **Auth Service**:
```bash
cd services/auth
python main.py
```

2. **API Gateway**:
```bash
cd services/gateway
python main.py
```

### Testing the APIs

Use the provided API client in `lib/api.ts`:

```typescript
import { authAPI, inboxAPI } from '@/lib/api'

// Login
const { access_token } = await authAPI.login('user@example.com', 'password')
localStorage.setItem('auth_token', access_token)

// Fetch inbox
const emails = await inboxAPI.list()
```

## Database Schema

### Auth Service (`auth_db`)
- `users` - User accounts
- `tokens` - Token storage

### Composer Service (`composer_db`)
- `drafts` - Email drafts
- `attachments` - Draft attachments metadata

### Storage Service (`storage_db`)
- `emails` - All emails
- `email_folders` - Folder organization
- `email_labels` - User labels

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/verify` - Verify token
- `POST /api/auth/logout` - Logout user

### Drafts
- `GET /api/drafts` - List drafts
- `POST /api/drafts` - Create draft
- `GET /api/drafts/{id}` - Get draft details
- `PUT /api/drafts/{id}` - Update draft
- `DELETE /api/drafts/{id}` - Delete draft
- `POST /api/drafts/{id}/send` - Send draft

### Inbox
- `GET /api/inbox` - List inbox emails
- `GET /api/emails/{id}` - Get email details
- `DELETE /api/emails/{id}` - Delete email
- `GET /api/search` - Search emails

### Sent/Trash
- `GET /api/sent` - List sent emails
- `GET /api/trash` - List trash emails

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `NEXT_PUBLIC_API_URL` - Frontend API endpoint
- `SECRET_KEY` - JWT signing key
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` - SMTP configuration
- `RABBITMQ_URL` - RabbitMQ connection string

## Deployment

### Frontend (Vercel)
```bash
# Connect to Vercel and deploy
vercel deploy
```

### Backend Services (Render)
Each service can be deployed to Render, Railway, or similar platforms:

1. Create a new Web Service
2. Connect to your Git repository
3. Set environment variables
4. Deploy

## Future Enhancements

- [ ] Real-time email notifications via WebSocket
- [ ] Email threading and conversation view
- [ ] Multiple account support
- [ ] Calendar integration
- [ ] Contact management
- [ ] Email templates
- [ ] IMAP/SMTP support for external accounts
- [ ] End-to-end encryption
- [ ] Advanced search filters
- [ ] Email signatures
- [ ] Rich text editor for composition
- [ ] Drag-and-drop file uploads
- [ ] Email scheduling
- [ ] Spam filtering
- [ ] Custom domains support

## Performance Optimization

- Database indexing for search
- Email pagination for large inboxes
- Redis caching for frequently accessed data
- Async email processing with RabbitMQ
- CDN for static assets
- Database connection pooling

## Security Considerations

- JWT token-based authentication
- Password hashing with bcrypt
- HTTPS in production
- Row-level security policies
- Input validation and sanitization
- CORS configuration
- Rate limiting on API endpoints
- Secure token storage in HTTP-only cookies (future)

## Monitoring and Logging

- Structured logging for all services
- Request/response logging in API Gateway
- Error tracking with Sentry (optional)
- Performance monitoring with tools like New Relic
- Database query logging for debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.
