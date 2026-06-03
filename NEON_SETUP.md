# Neon Database Setup Guide

## SQL to Create Tables

Run this SQL in your Neon database console:

```sql
-- Create users table
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  name TEXT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  email_verified BOOLEAN DEFAULT FALSE,
  image TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create emails table
CREATE TABLE emails (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  "from" TEXT NOT NULL,
  from_name TEXT,
  "to" TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  preview TEXT,
  read BOOLEAN DEFAULT FALSE,
  archived BOOLEAN DEFAULT FALSE,
  deleted BOOLEAN DEFAULT FALSE,
  is_draft BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_emails_user_id ON emails(user_id);
CREATE INDEX idx_emails_created_at ON emails(created_at DESC);
```

## Steps to Set Up

1. **Create the tables**: Go to your Neon dashboard and run the SQL above in the SQL editor
2. **Update environment variables**: Make sure these are set in your `.env.local`:
   - `DATABASE_URL`: Your Neon connection string (already set)
   - `JWT_SECRET`: A secure random string (already set to a default, change in production)

3. **Start the development server**:
   ```bash
   pnpm dev
   ```

4. **Test the authentication**:
   - Go to `http://localhost:3000/signup`
   - Create a new account
   - You'll get a JWT token that's stored in localStorage

5. **JWT Token Details**:
   - Tokens are valid for 7 days
   - Stored in browser's localStorage as `token`
   - Sent via `Authorization: Bearer <token>` header in API requests
   - Change `JWT_SECRET` in `.env.local` for production

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Create new account
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "name": "User Name"
  }
  ```
  
- `POST /api/auth/login` - Login
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```

### Emails (requires JWT token in Authorization header)
- `GET /api/emails` - Fetch user's emails
- `POST /api/emails` - Create new email
  ```json
  {
    "to": "recipient@example.com",
    "subject": "Email subject",
    "body": "Email content"
  }
  ```
- `DELETE /api/emails/:id` - Delete email

## Architecture

- **Auth**: JWT-based with bcrypt password hashing
- **Database**: Neon PostgreSQL with Drizzle ORM
- **Frontend**: Next.js 16 with SWR for data fetching
- **Storage**: localStorage for JWT tokens (client-side only)

## Troubleshooting

If you get database errors:
1. Verify tables were created in Neon
2. Check `DATABASE_URL` is correct in `.env.local`
3. Ensure you have network access to Neon from your app
4. Check JWT_SECRET is set in environment variables
