# MicroMail Architecture

## System Overview

MicroMail is a Gmail-like webmail platform built with a microservices architecture. The system is designed for scalability, reliability, and independent service deployment.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                           │
│  Login | Register | Inbox | Sent | Drafts | Trash | Compose     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   API Gateway (FastAPI)                          │
│  ├─ Routes requests to services                                  │
│  ├─ Authenticates requests (JWT)                                │
│  ├─ Rate limiting & logging                                     │
│  └─ Error handling & response normalization                     │
└──────┬──────────┬──────────┬──────────┬──────────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
   ┌─────────┬──────────┬──────────┬──────────┐
   │  Auth   │ Composer │ Storage  │ Delivery │
   │ Service │ Service  │ Service  │ Service  │
   └─────────┴──────────┴──────────┴──────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
   ┌─────────┬──────────┬──────────┐
   │ auth_db │composer_ │storage_  │
   │         │   db     │   db     │
   └─────────┴──────────┴──────────┘

          RabbitMQ Event Bus (async communication)
   ┌─────────────────────────────────────────────┐
   │ email.send → email.delivered/email.failed   │
   │ draft.created → draft.updated → draft.sent  │
   └─────────────────────────────────────────────┘
```

## Architecture Principles

### 1. Microservices Pattern

**Why?**
- Independent scaling
- Technology flexibility
- Fault isolation
- Easy deployment

**Implementation:**
- Each service has its own codebase
- Services communicate via API Gateway or events
- Horizontal scaling possible

### 2. Database-per-Service Pattern

**Why?**
- Data ownership
- Schema flexibility
- Loose coupling

**Databases:**
```
Auth Service    → auth_db (users, sessions)
Composer Service → composer_db (drafts, attachments)
Storage Service → storage_db (emails, folders, labels)
Delivery Service → (no database, reads from events)
```

### 3. CQRS (Command Query Responsibility Segregation)

**Applied to Storage Service:**

**Write Model:**
- Receives events from Delivery Service
- Stores emails in database
- Publishes `email.stored` event

**Read Model:**
- Serves email list/search queries
- Optimized for fast queries
- Separate tables for different queries

### 4. Event-Driven Architecture

**Benefits:**
- Async processing
- Service decoupling
- Audit trail
- Easier scaling

**Event Types:**
```
Authentication:
- user.registered
- user.logged_in
- user.logged_out

Drafts:
- draft.created
- draft.updated
- draft.deleted
- draft.sent

Emails:
- email.send (from Composer)
- email.delivered (from Delivery)
- email.failed (from Delivery)
- email.stored (from Storage)
```

### 5. JWT Token-Based Authentication

**Flow:**
1. User registers/logs in
2. Auth Service generates JWT token
3. Token stored in client localStorage
4. Token sent with each API request
5. Gateway validates token before routing

**Token Structure:**
```
{
  "sub": "user_id",
  "exp": 1705328400,
  "type": "access" | "refresh",
  "iat": 1705324800
}
```

## Service Architecture

### API Gateway

**Responsibilities:**
- Request routing to correct service
- Authentication & authorization
- Rate limiting
- Request/response logging
- Error handling & normalization
- CORS configuration

**Tech Stack:**
- FastAPI
- Python-jose (JWT)
- Pydantic (validation)

**Routes:**
```
POST   /api/auth/register       → Auth Service
POST   /api/auth/login          → Auth Service
POST   /api/auth/refresh        → Auth Service
GET    /api/inbox               → Storage Service
GET    /api/sent                → Storage Service
GET    /api/drafts              → Composer Service
POST   /api/drafts              → Composer Service
POST   /api/drafts/{id}/send    → Composer Service
```

### Auth Service

**Responsibilities:**
- User registration
- Login/logout
- Password hashing (bcrypt)
- Token generation (JWT)
- Token validation

**Database Schema (auth_db):**
```sql
users:
  id (UUID primary)
  name (string)
  email (string unique)
  password_hash (string)
  created_at (timestamp)

tokens:
  user_id (UUID foreign)
  refresh_token (text)
  created_at (timestamp)
  expires_at (timestamp)
```

**Security:**
- Passwords hashed with bcrypt (not stored plaintext)
- JWT tokens signed with SECRET_KEY
- Refresh tokens stored for revocation
- Access tokens expire after 30 minutes
- Refresh tokens expire after 7 days

### Composer Service

**Responsibilities:**
- Draft creation & editing
- Draft deletion
- Draft sending (publishes email.send event)
- Attachment metadata

**Database Schema (composer_db):**
```sql
drafts:
  id (UUID primary)
  user_id (UUID foreign)
  to (email)
  cc (email[])
  bcc (email[])
  subject (string)
  body (text)
  created_at (timestamp)
  updated_at (timestamp)

attachments:
  id (UUID primary)
  draft_id (UUID foreign)
  filename (string)
  size (integer)
  mime_type (string)
  s3_key (string)
```

**Workflow:**
1. User creates draft via UI
2. Draft stored in database
3. Publishes `draft.created` event
4. User edits draft
5. Publishes `draft.updated` event
6. User clicks "Send"
7. Publishes `draft.sent` → `email.send` event
8. Draft deleted from database

### Storage Service

**Responsibilities:**
- Email storage (CQRS read model)
- Email retrieval & listing
- Email search
- Email deletion/archiving

**Database Schema (storage_db):**
```sql
emails:
  id (UUID primary)
  user_id (UUID foreign)
  from_email (email)
  from_name (string)
  to (email)
  cc (email[])
  bcc (email[])
  subject (string)
  body (text)
  preview (string)
  timestamp (timestamp)
  folder (enum: inbox/sent/trash/archive)
  read (boolean)
  starred (boolean)
  labels (string[])
  created_at (timestamp)

email_indices:
  user_id, folder (for listing)
  user_id, timestamp (for sorting)
  user_id, read (for unread count)
  full_text_search (subject, body)
```

**Read Operations:**
- List inbox emails (paginated, sortable)
- Get email details
- Search emails (full-text search)
- Get unread count

### Delivery Service

**Responsibilities:**
- Consume `email.send` events from RabbitMQ
- Send emails via SMTP
- Retry failed deliveries
- Publish `email.delivered`/`email.failed` events

**Workflow:**
1. Storage Service publishes `email.send` event
2. Delivery Service consumes event
3. Validates recipient email
4. Sends via SMTP provider (Gmail, SendGrid, etc.)
5. If successful:
   - Publishes `email.delivered` event
   - Storage Service stores email in "sent" folder
6. If failed:
   - Publishes `email.failed` event
   - Retry with exponential backoff
   - After max retries, mark as permanently failed

**SMTP Providers (Recommended):**
- SendGrid (scalable, reliable)
- AWS SES (integrated with AWS)
- Mailgun (developer-friendly)
- Gmail API (for testing)

## Data Flow Examples

### Example 1: User Registration

```
1. User fills form on /register
2. Frontend calls POST /api/auth/register
3. API Gateway routes to Auth Service
4. Auth Service:
   - Validates email not duplicate
   - Hashes password with bcrypt
   - Creates user in auth_db
   - Generates access + refresh tokens
5. Returns tokens to frontend
6. Frontend stores token in localStorage
7. Frontend redirects to /mail/inbox
```

### Example 2: Sending an Email

```
1. User clicks "Send" in composer
2. Frontend calls POST /api/drafts/{id}/send
3. API Gateway routes to Composer Service
4. Composer Service:
   - Validates draft exists
   - Publishes email.send event to RabbitMQ
   - Deletes draft from database
5. Delivery Service:
   - Consumes email.send event
   - Sends via SMTP
6. On success:
   - Publishes email.delivered event
7. Storage Service:
   - Consumes email.delivered event
   - Stores email in "sent" folder
8. Frontend shows "Email sent" notification
```

### Example 3: Reading an Email

```
1. User clicks email in inbox
2. Frontend calls GET /api/emails/{id}
3. API Gateway routes to Storage Service
4. Storage Service:
   - Returns full email details
   - (Could also call POST /mark-read)
5. Frontend displays email
6. User can reply/forward/archive
```

## RabbitMQ Event System

### Exchange Configuration

**Type:** Topic Exchange (routing by topic)

**Routing Keys:**
```
user.*              (user.registered, user.logged_in)
draft.*             (draft.created, draft.updated, draft.sent)
email.*             (email.send, email.delivered, email.failed)
```

### Queue Configuration

Each service has its own queue:
```
auth-service-queue       → Listens to: user.* events
composer-service-queue   → Listens to: draft.* events
storage-service-queue    → Listens to: email.delivered
delivery-service-queue   → Listens to: email.send
```

### Message Format

```json
{
  "event_type": "email.send",
  "email_id": "uuid",
  "user_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "from": "user@micromail.com",
    "to": "recipient@example.com",
    "subject": "Hello",
    "body": "Message content"
  }
}
```

## Scaling Strategy

### Horizontal Scaling

**Frontend:**
- Deploy to Vercel (auto-scaling)
- CDN for static assets
- Can handle millions of users

**API Gateway:**
- Deploy multiple instances
- Load balancer in front
- Share Redis for session storage

**Microservices:**
```
Auth Service       → Usually 1-2 instances (low traffic)
Composer Service   → 1-3 instances (moderate traffic)
Storage Service    → 2-5 instances (high traffic)
Delivery Service   → 5-10 instances (async processing)
```

### Vertical Scaling

- Increase database connections
- More CPU for processing
- More memory for caching

### Database Optimization

- Indexing on frequently queried fields
- Connection pooling
- Read replicas for heavy queries
- Caching layer (Redis)

## Security Considerations

### Authentication & Authorization

- [x] JWT tokens for stateless auth
- [x] Password hashing with bcrypt
- [x] Refresh token mechanism
- [x] Token expiration & validation
- [ ] OAuth2 for social login (future)
- [ ] Multi-factor authentication (future)

### Data Protection

- [x] HTTPS in production
- [x] SQL parameter binding (prevent injection)
- [x] Input validation with Pydantic
- [x] CORS configuration
- [ ] End-to-end encryption (future)
- [ ] Attachment scanning (future)

### API Security

- [x] Rate limiting
- [x] Request logging
- [x] Error message sanitization
- [ ] API key management (future)
- [ ] Web Application Firewall (future)

## Monitoring & Logging

### Logging Strategy

**Services log:**
- Request/response details
- Errors and exceptions
- Business events (email sent, etc.)
- Performance metrics

**Aggregation:**
- ELK Stack (Elasticsearch, Logstash, Kibana)
- DataDog
- New Relic
- CloudWatch (AWS)

### Metrics to Monitor

```
Application:
- Login success/failure rate
- Email send success rate
- Average response time
- Error rates by endpoint

Infrastructure:
- Database connection pool usage
- RabbitMQ queue depth
- Service uptime
- Memory/CPU usage
```

## Deployment

### Development Environment

```bash
docker-compose up -d
# All services running locally
```

### Staging Environment

- Frontend: Vercel (staging branch)
- Services: Render, Railway, or AWS ECS
- Databases: Neon (PostgreSQL), Upstash (Redis)
- RabbitMQ: CloudAMQP

### Production Environment

- **Frontend:** Vercel
- **API Gateway:** AWS ECS/Fargate or similar
- **Microservices:** Kubernetes or managed container services
- **Databases:** AWS RDS PostgreSQL with multi-AZ
- **Cache:** AWS ElastiCache (Redis)
- **Message Queue:** AWS SQS + SNS or AWS MQ
- **Storage:** AWS S3 for attachments
- **DNS/CDN:** Route 53 + CloudFront
- **Monitoring:** CloudWatch, DataDog, or New Relic

## Future Enhancements

### Short Term (3-6 months)
- [x] Core email functionality
- [ ] Real-time notifications (WebSocket)
- [ ] Email threading/conversations
- [ ] Rich text editor
- [ ] Attachment upload

### Medium Term (6-12 months)
- [ ] Multiple account support
- [ ] Calendar integration
- [ ] Contact management
- [ ] Email templates
- [ ] IMAP/SMTP support (external accounts)

### Long Term (12+ months)
- [ ] End-to-end encryption
- [ ] Advanced search filters
- [ ] Custom domains
- [ ] Email scheduling
- [ ] Spam filtering
- [ ] Mobile app (React Native)

## Technology Stack

### Frontend
- **Framework:** Next.js 16
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui
- **Form:** React Hook Form
- **HTTP Client:** Fetch API

### Backend
- **Framework:** FastAPI (Python 3.11)
- **Validation:** Pydantic
- **Auth:** python-jose (JWT)
- **Security:** Passlib (bcrypt)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (optional)
- **Message Queue:** RabbitMQ

### Infrastructure
- **Containerization:** Docker
- **Orchestration:** Docker Compose (dev), Kubernetes (prod)
- **Database:** PostgreSQL 16
- **Cache:** Redis (future)
- **Message Queue:** RabbitMQ 3.12

## References

- [Microservices Architecture](https://microservices.io/)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
- [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Saga Pattern for Transactions](https://microservices.io/patterns/data/saga.html)
- [JWT Authentication](https://tools.ietf.org/html/rfc7519)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)

---

For questions about architecture, see README.md or GETTING_STARTED.md.
