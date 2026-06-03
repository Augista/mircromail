# MicroMail API Documentation

## API Gateway (Port 8000)

The API Gateway serves as the single entry point for all frontend requests. It routes requests to appropriate microservices and handles authentication.

### Base URL
```
http://localhost:8000
```

### Response Format
All responses are JSON with the following structure:

**Success:**
```json
{
  "data": {},
  "status": "ok"
}
```

**Error:**
```json
{
  "detail": "Error message",
  "status": "error"
}
```

---

## Authentication Endpoints

### Register
**Endpoint:** `POST /api/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secure_password_123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Status Codes:**
- `200` - Registration successful
- `400` - Email already registered or validation error
- `422` - Invalid request body

---

### Login
**Endpoint:** `POST /api/auth/login`

Login with email and password.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "secure_password_123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Status Codes:**
- `200` - Login successful
- `401` - Invalid credentials
- `422` - Invalid request body

---

### Refresh Token
**Endpoint:** `POST /api/auth/refresh`

Get a new access token using a refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Status Codes:**
- `200` - Token refreshed successfully
- `401` - Invalid refresh token

---

### Verify Token
**Endpoint:** `POST /api/auth/verify`

Verify an access token and get user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Status Codes:**
- `200` - Token valid
- `401` - Invalid or expired token
- `404` - User not found

---

### Logout
**Endpoint:** `POST /api/auth/logout`

Logout and invalidate tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "ok",
  "message": "Successfully logged out"
}
```

**Status Codes:**
- `200` - Logout successful
- `401` - Invalid token

---

## Drafts Endpoints

All drafts endpoints require authentication.

### List Drafts
**Endpoint:** `GET /api/drafts`

List all email drafts for the authenticated user.

**Query Parameters:**
- `page` (optional) - Page number (default: 1)
- `limit` (optional) - Results per page (default: 20)

**Response:**
```json
{
  "drafts": [
    {
      "id": "draft_123",
      "to": "recipient@example.com",
      "subject": "Meeting Tomorrow",
      "body": "Just confirming...",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 20
}
```

---

### Create Draft
**Endpoint:** `POST /api/drafts`

Create a new email draft.

**Request Body:**
```json
{
  "to": "recipient@example.com",
  "subject": "Meeting Tomorrow",
  "body": "Just confirming our meeting tomorrow at 2 PM.",
  "cc": "cc@example.com",
  "bcc": "bcc@example.com"
}
```

**Response:**
```json
{
  "id": "draft_123",
  "to": "recipient@example.com",
  "subject": "Meeting Tomorrow",
  "body": "Just confirming our meeting tomorrow at 2 PM.",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### Get Draft
**Endpoint:** `GET /api/drafts/{draft_id}`

Get a specific draft by ID.

**Response:**
```json
{
  "id": "draft_123",
  "to": "recipient@example.com",
  "subject": "Meeting Tomorrow",
  "body": "Just confirming...",
  "cc": "cc@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### Update Draft
**Endpoint:** `PUT /api/drafts/{draft_id}`

Update an existing draft.

**Request Body:**
```json
{
  "to": "recipient@example.com",
  "subject": "Updated Subject",
  "body": "Updated message body"
}
```

---

### Delete Draft
**Endpoint:** `DELETE /api/drafts/{draft_id}`

Delete a draft permanently.

**Response:**
```json
{
  "status": "ok",
  "message": "Draft deleted successfully"
}
```

---

### Send Draft
**Endpoint:** `POST /api/drafts/{draft_id}/send`

Send a draft email. This publishes an event to RabbitMQ for the delivery service.

**Response:**
```json
{
  "status": "ok",
  "message": "Email sent successfully",
  "email_id": "email_456"
}
```

---

## Inbox Endpoints

All inbox endpoints require authentication.

### List Inbox Emails
**Endpoint:** `GET /api/inbox`

List emails in the inbox.

**Query Parameters:**
- `page` (optional) - Page number (default: 1)
- `limit` (optional) - Results per page (default: 20)
- `sort` (optional) - Sort field (default: timestamp)
- `order` (optional) - Sort order: asc/desc (default: desc)

**Response:**
```json
{
  "emails": [
    {
      "id": "email_123",
      "from": "john@example.com",
      "from_name": "John Doe",
      "subject": "Project Update",
      "preview": "Just wanted to follow up...",
      "timestamp": "2024-01-15T10:30:00Z",
      "read": false,
      "has_attachments": false
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 20,
  "unread_count": 5
}
```

---

### Get Email Details
**Endpoint:** `GET /api/emails/{email_id}`

Get full details of an email.

**Response:**
```json
{
  "id": "email_123",
  "from": "john@example.com",
  "from_name": "John Doe",
  "to": "you@example.com",
  "cc": ["cc@example.com"],
  "bcc": ["bcc@example.com"],
  "subject": "Project Update",
  "body": "Full HTML body content",
  "text_body": "Plain text version",
  "timestamp": "2024-01-15T10:30:00Z",
  "read": false,
  "starred": false,
  "archived": false,
  "folder": "inbox",
  "labels": ["work", "important"],
  "attachments": [
    {
      "id": "attach_123",
      "filename": "document.pdf",
      "size": 102400,
      "mime_type": "application/pdf"
    }
  ]
}
```

---

### Search Emails
**Endpoint:** `GET /api/search`

Search emails by query.

**Query Parameters:**
- `q` (required) - Search query
- `folder` (optional) - Folder to search in
- `from` (optional) - Filter by sender
- `to` (optional) - Filter by recipient
- `subject` (optional) - Filter by subject
- `before` (optional) - Before date (ISO 8601)
- `after` (optional) - After date (ISO 8601)
- `has` (optional) - Has attachment (true/false)

**Response:**
```json
{
  "emails": [...],
  "total": 10,
  "query": "project"
}
```

---

### Delete Email
**Endpoint:** `DELETE /api/emails/{email_id}`

Delete an email (moves to trash).

**Response:**
```json
{
  "status": "ok",
  "message": "Email deleted successfully"
}
```

---

## Sent Emails Endpoints

### List Sent Emails
**Endpoint:** `GET /api/sent`

List emails in the sent folder.

**Query Parameters:** Same as inbox listing

---

## Trash Endpoints

### List Trash Emails
**Endpoint:** `GET /api/trash`

List emails in the trash folder.

**Query Parameters:** Same as inbox listing

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Detailed error message",
  "status": "error",
  "code": "INVALID_REQUEST"
}
```

### Common Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Too Many Requests (Rate Limited)
- `500` - Internal Server Error
- `502` - Bad Gateway
- `503` - Service Unavailable

---

## Authentication

### Token-based Authentication

All protected endpoints require an `Authorization` header with a Bearer token:

```
Authorization: Bearer <access_token>
```

### Token Format

Tokens are JWT (JSON Web Tokens) with the following claims:
- `sub` - User ID
- `exp` - Expiration time
- `type` - Token type (access/refresh)

---

## Rate Limiting

Rate limits are enforced by the API Gateway:
- **Default:** 100 requests per minute
- **Auth endpoints:** 10 requests per minute
- **Search:** 30 requests per minute

Rate limit information is included in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705328400
```

---

## Examples

### Complete Login Flow

1. Register:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

2. Login:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

3. Use token to fetch inbox:
```bash
curl -X GET http://localhost:8000/api/inbox \
  -H "Authorization: Bearer <access_token>"
```

### Send Email

1. Create draft:
```bash
curl -X POST http://localhost:8000/api/drafts \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Hello",
    "body": "This is my message"
  }'
```

2. Send draft:
```bash
curl -X POST http://localhost:8000/api/drafts/<draft_id>/send \
  -H "Authorization: Bearer <access_token>"
```

---

## Webhooks (Future)

Support for webhooks to notify external systems of email events:
- Email received
- Email sent
- Email delivery failed
- Email read

---

## Version

Current API Version: `v1`

For version-specific endpoints, use: `/api/v1/...`

---

## Support

For API issues, contact support@micromail.dev or open an issue on GitHub.
