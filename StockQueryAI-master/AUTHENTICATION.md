# Authentication System Guide - StockQuery AI

## Overview

The StockQuery AI application now includes a complete authentication system with JWT (JSON Web Tokens), secure password hashing, and user-specific query history. This guide explains how the system works and how to set it up.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ App.jsx (Main App)                                     │ │
│  │ ├─ AuthModal.jsx (Login/Register UI)                  │ │
│  │ ├─ Sidebar.jsx (Navigation)                           │ │
│  │ └─ Other Components                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│           ↓ (axios with interceptors)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ services/api.js (Centralized API Client)              │ │
│  │ ├─ Base URL: http://localhost:8000                    │ │
│  │ ├─ Auto-adds JWT token to headers                     │ │
│  │ └─ Handles 401 errors                                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
           ↓ (HTTP/REST API)
┌─────────────────────────────────────────────────────────────┐
│                Backend (FastAPI + Python)                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ main.py (FastAPI Application)                         │ │
│  │ ├─ POST /register - User registration                 │ │
│  │ ├─ POST /login - User login                           │ │
│  │ ├─ POST /query - Query with JWT protection            │ │
│  │ ├─ GET /history - Get user query history              │ │
│  │ └─ Authentication utilities (JWT, bcrypt)             │ │
│  └────────────────────────────────────────────────────────┘ │
│           ↓ (MCP JSON-RPC)                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ MCP Server (port 8001)                                │ │
│  │ ├─ register_user() - Insert user in DB                │ │
│  │ ├─ authenticate_user() - Get user by email            │ │
│  │ ├─ save_query_history() - Store queries               │ │
│  │ ├─ get_query_history() - Retrieve user queries        │ │
│  │ └─ Other inventory tools                              │ │
│  └────────────────────────────────────────────────────────┘ │
│           ↓ (SQLite)                                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Database (inventory.db)                               │ │
│  │ ├─ users table (id, email, password_hash)             │ │
│  │ ├─ query_history table (user_id, question, answer)    │ │
│  │ └─ products table (existing)                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Authentication Flow

### 1. Registration Flow

```
User fills register form
    ↓
Frontend validates email & password (min 6 chars)
    ↓
POST /register with { email, password }
    ↓
Backend hashes password with bcrypt
    ↓
MCP inserts user into SQLite
    ↓
Success → Show "Login" prompt
Error → Show error message (e.g., "Email already exists")
```

### 2. Login Flow

```
User enters email & password
    ↓
Frontend validates inputs
    ↓
POST /login with { email, password }
    ↓
Backend retrieves user from MCP
    ↓
Verify password hash with bcrypt
    ↓
Create JWT token (expires in 7 days)
    ↓
Return { access_token, token_type, email }
    ↓
Frontend stores token & email in localStorage
    ↓
Frontend redirects to main app
    ↓
User's previous queries loaded
```

### 3. Protected Request Flow

```
User submits query
    ↓
Frontend checks localStorage for token
    ↓
api.js interceptor adds: Authorization: Bearer <token>
    ↓
POST /query with JWT header
    ↓
Backend verifies JWT signature & expiration
    ↓
If valid:
   - Execute query
   - Save to query_history with user_id
   - Return response
    ↓
If invalid:
   - Return 401 Unauthorized
   - Frontend clears localStorage
   - Redirect to login
```

## Installation & Setup

### 1. Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

### 2. Configure Environment Variables

**Backend (.env)**
```bash
# Copy .env.example to .env and fill in:
NEBIUS_API_KEY=your-nebius-api-key
JWT_SECRET=your-super-secret-jwt-key
ELEVENLABS_API_KEY=optional
ELEVENLABS_VOICE_ID=optional
```

**Frontend (.env.local)**
```bash
# Create .env.local from .env.example:
VITE_API_URL=http://localhost:8000
```

### 3. Start the Services

```bash
# Terminal 1: Start MCP Server (port 8001)
cd mcp_server
python server.py

# Terminal 2: Start FastAPI Backend (port 8000)
cd backend
python main.py

# Terminal 3: Start React Frontend (port 5173)
cd frontend
npm run dev
```

### 4. Access the Application

Open http://localhost:5173 in your browser. You'll see the login/register modal.

## API Endpoints

### Authentication Endpoints

#### POST /register
Register a new user

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (Success):**
```json
{
  "success": true,
  "user_id": 1
}
```

**Response (Error):**
```json
{
  "detail": "Email already exists."
}
```

#### POST /login
Authenticate a user

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "email": "user@example.com"
}
```

**Response (Error):**
```json
{
  "detail": "Invalid email or password"
}
```

#### GET /history
Get user's query history (Protected)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "question": "Which products are low in stock?",
    "answer": "Based on the inventory...",
    "tool_used": "search_inventory",
    "timestamp": "2026-04-25T10:30:00"
  }
]
```

#### POST /query
Submit a query (Optional Auth)

**Headers:**
```
Authorization: Bearer <access_token>  # Optional but recommended
```

**Request:**
```json
{
  "question": "Show me all Dairy products"
}
```

**Response:**
```json
{
  "answer": "Here are the Dairy products...",
  "tool_used": "search_inventory",
  "data": [...]
}
```

## Frontend Components

### AuthModal.jsx
Handles login and registration UI

**Props:**
- `isOpen` (bool): Show/hide modal
- `onClose` (function): Callback when user closes modal
- `onAuthSuccess` (function): Callback after successful login

**Validation:**
- Email format validation
- Password minimum 6 characters
- Password confirmation match (on register)
- Name required (on register)

**Features:**
- Toggle between login and register modes
- Real-time error messages
- Success message after registration
- Loading state feedback
- Disabled inputs during submission

### services/api.js
Centralized API client using axios

**Features:**
- Auto-adds JWT token to all requests
- Handles 401 responses (clears token and redirects)
- Configurable base URL via env variable
- Timeout set to 30 seconds

**Usage:**
```javascript
import api from './services/api'

// Auto-includes token in Authorization header
const { data } = await api.post('/query', { question: 'Show all products' })
```

## Security Considerations

### Password Storage
- Passwords are **never** stored in plain text
- Bcrypt hashing with salt (10 rounds by default)
- Password is verified during login before JWT creation

### JWT Token
- 7-day expiration
- Secret key should be strong (min 32 characters)
- Signed with HS256 algorithm
- Stored in localStorage (accessible via JS, not HttpOnly for now)

### CORS
- Only accepts requests from `http://localhost:5173`
- Can be updated for production URLs

### Best Practices Implemented
✓ Passwords hashed with bcrypt
✓ JWT tokens with expiration
✓ Protected routes require authentication
✓ User input validation (frontend & backend)
✓ 401 error handling with automatic logout
✓ Secure header transmission
✓ CORS configuration
✓ User-specific data isolation

## Common Issues & Solutions

### Issue: "Email already exists"
**Solution:** The email is already registered. Try logging in or use a different email.

### Issue: "Invalid email or password"
**Solution:** Check that your email and password are correct. Passwords are case-sensitive.

### Issue: "401 Unauthorized" error
**Solution:** 
- Your token has expired (7 days). Login again.
- Or the JWT_SECRET in backend doesn't match.

### Issue: Cannot connect to backend
**Solution:**
- Check that FastAPI is running on port 8000
- Check CORS origins in main.py if accessing from different URL
- Check firewall settings

### Issue: MCP Server errors
**Solution:**
- Make sure MCP Server is running on port 8001
- Check database permissions on inventory.db
- Check that users table was created

## Database Schema

### users table
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### query_history table
```sql
CREATE TABLE query_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  tool_used TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (id)
)
```

## Future Enhancements

- [ ] Email verification
- [ ] Password reset functionality
- [ ] Two-factor authentication (2FA)
- [ ] OAuth integration (Google, GitHub)
- [ ] Refresh token rotation
- [ ] Account deletion
- [ ] Audit logs
- [ ] User roles and permissions
- [ ] Rate limiting per user
- [ ] Session management (max sessions)
- [ ] HttpOnly cookies for tokens (more secure than localStorage)
- [ ] CSRF protection

## Testing the System

### Test Registration
1. Open http://localhost:5173
2. Click "Create Account"
3. Fill in email, password (min 6 chars)
4. Click "Register"
5. See success message
6. Automatically switches to login mode
7. Login with same credentials

### Test Login
1. After registration, login with your email and password
2. You should be redirected to main app
3. Your email shows in top-right
4. Try querying - it saves to your history

### Test Protected Routes
1. Login to get a token
2. Open browser DevTools → Storage → localStorage
3. Note the token value
4. Copy the token
5. Manually verify it works: Add Authorization header in API request

### Test Token Expiration
1. Wait for token to expire (7 days) or manually modify expiration in backend
2. Try to submit a query
3. Should see 401 error and redirect to login

## Production Checklist

Before deploying to production:

- [ ] Change JWT_SECRET to a strong random value (min 32 chars)
- [ ] Update CORS origins to production domain
- [ ] Use HTTPS (not HTTP)
- [ ] Switch to HttpOnly cookies for tokens
- [ ] Add email verification
- [ ] Add password reset functionality
- [ ] Set up rate limiting
- [ ] Enable CSRF protection
- [ ] Use environment-specific .env files
- [ ] Test with production-level load
- [ ] Set up monitoring and logging
- [ ] Regular security audits
- [ ] Update dependencies regularly

## Support & Questions

For issues or questions:
1. Check the Common Issues section above
2. Review the API endpoints documentation
3. Check backend logs for errors
4. Check browser console for frontend errors
5. Verify all services are running on correct ports
