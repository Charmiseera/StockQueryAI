# Developer's Guide - Extending the Authentication System

## Overview

This guide is for developers who want to extend, customize, or troubleshoot the authentication system. It provides deep dives into each component and shows how to make common modifications.

## Table of Contents

1. [Architecture Deep Dive](#architecture-deep-dive)
2. [Component Breakdown](#component-breakdown)
3. [Common Customizations](#common-customizations)
4. [Adding Features](#adding-features)
5. [Testing & Debugging](#testing--debugging)
6. [Performance Optimization](#performance-optimization)

## Architecture Deep Dive

### Authentication Flow (Detailed)

#### Registration Process

1. **Frontend Validation**
   - Email format: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`
   - Password length: `>= 6 characters`
   - Name: `required, non-empty`
   - Passwords: `must match`

2. **API Call**
   ```javascript
   POST /register
   {
     "email": "user@example.com",
     "password": "securepassword123"
   }
   ```

3. **Backend Processing**
   - Hash password: `pwd_context.hash(password)` (bcrypt, 10 rounds)
   - Call MCP tool: `register_user(email, password_hash)`

4. **MCP Server Processing**
   - Check email uniqueness: `SELECT * FROM users WHERE email = ?`
   - If exists: return error
   - If new: `INSERT INTO users (email, password_hash) VALUES (?, ?)`

5. **Response**
   ```json
   {
     "success": true,
     "user_id": 1
   }
   ```

#### Login Process

1. **API Call**
   ```javascript
   POST /login
   {
     "email": "user@example.com",
     "password": "securepassword123"
   }
   ```

2. **Backend Processing**
   - Authenticate: `mcp_manager.call_tool("authenticate_user", {"email": email})`
   - MCP returns: `{id, email, password_hash}`

3. **Password Verification**
   ```python
   verified = pwd_context.verify(password, stored_hash)
   if not verified:
       raise HTTPException(401, "Invalid email or password")
   ```

4. **Token Creation**
   ```python
   token = create_access_token({
       "user_id": user["id"],
       "email": user["email"]
   })
   # Token expires in 7 days
   ```

5. **Response**
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer",
     "email": "user@example.com"
   }
   ```

### Token Validation (Protected Requests)

1. **Frontend sends request with token**
   ```javascript
   Authorization: Bearer <token>
   ```

2. **Backend receives request**
   ```python
   authorization: str = Header(None)
   token = authorization.split(" ")[1]  # Extract from "Bearer <token>"
   ```

3. **JWT Verification**
   ```python
   payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
   # Checks:
   # - Signature is valid
   # - Expiration time not passed
   # - Algorithm matches
   ```

4. **Extract User Info**
   ```python
   user_id = payload["user_id"]
   email = payload["email"]
   ```

5. **Proceed with Request**
   - Save query with `user_id`
   - Return user-specific data

## Component Breakdown

### 1. Frontend - AuthModal.jsx

**Key Functions:**

```javascript
// Validation
validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
}

validatePassword(pwd) {
    return pwd.length >= 6
}

validateForm() {
    // Checks all fields and returns boolean
}

// Submission
async handleSubmit(e) {
    // Calls /register or /login
    // Stores token in localStorage
}

// Mode switching
toggleMode() {
    // Switch between login and register
    // Clear form fields
}
```

**State Management:**
```javascript
const [isLogin, setIsLogin] = useState(true)
const [email, setEmail] = useState('')
const [password, setPassword] = useState('')
const [confirmPassword, setConfirmPassword] = useState('')
const [loading, setLoading] = useState(false)
const [error, setError] = useState(null)
const [successMsg, setSuccessMsg] = useState(null)
```

### 2. Frontend - services/api.js

**Axios Instance:**
```javascript
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' }
})
```

**Request Interceptor:**
```javascript
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})
```

**Response Interceptor:**
```javascript
api.interceptors.response.use((response) => {
    return response
}, (error) => {
    if (error.response?.status === 401) {
        // Clear stored data
        localStorage.removeItem('token')
        localStorage.removeItem('email')
        // Redirect to login
        window.location.href = '/'
    }
    return Promise.reject(error)
})
```

### 3. Backend - main.py

**JWT Functions:**
```python
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except:
        return None
```

**Endpoints:**
```python
@app.post("/register")
async def register(auth: UserAuth):
    # Hash password
    # Call MCP register_user
    # Return user_id or error

@app.post("/login")
async def login(auth: UserAuth):
    # Get user from MCP
    # Verify password
    # Create JWT token
    # Return token

@app.get("/history")
async def get_history(authorization: str = Header(None)):
    # Get current user
    # Get history from MCP
    # Return history
```

### 4. MCP Server - server.py

**User Database Functions:**
```python
@mcp.tool()
def register_user(email: str, password_hash: str) -> dict:
    """Register a new user with hashed password"""
    try:
        conn.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)",
                    (email, password_hash))
        conn.commit()
        return {"success": True, "user_id": last_id}
    except sqlite3.IntegrityError:
        return {"error": "Email already exists."}

@mcp.tool()
def authenticate_user(email: str) -> dict:
    """Get user details for login"""
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else {"error": "User not found."}

@mcp.tool()
def save_query_history(user_id: int, question: str, answer: str, tool_used: str) -> dict:
    """Save query to history"""
    conn.execute(
        "INSERT INTO query_history (user_id, question, answer, tool_used) VALUES (?, ?, ?, ?)",
        (user_id, question, answer, tool_used)
    )
    conn.commit()
    return {"success": True}

@mcp.tool()
def get_query_history(user_id: int) -> list[dict]:
    """Get user's query history"""
    rows = conn.execute(
        "SELECT * FROM query_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 50",
        (user_id,)
    ).fetchall()
    return _rows(rows)
```

## Common Customizations

### 1. Change Token Expiration

**File**: `backend/main.py`

Find:
```python
expire = datetime.utcnow() + timedelta(days=7)
```

Change to:
```python
expire = datetime.utcnow() + timedelta(days=30)  # 30 days
# or
expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour
```

### 2. Enforce Stronger Passwords

**File**: `frontend/src/components/AuthModal.jsx`

Find:
```javascript
const validatePassword = (pwd) => {
    return pwd.length >= 6
}
```

Change to:
```javascript
const validatePassword = (pwd) => {
    // Require: min 8 chars, 1 uppercase, 1 number, 1 special char
    return /^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/.test(pwd)
}
```

### 3. Add User Profile Fields

**Database Migration** (Add to users table):
```sql
ALTER TABLE users ADD COLUMN full_name TEXT;
ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
```

**API Update**: Modify `register_user()` MCP tool:
```python
@mcp.tool()
def register_user(email: str, password_hash: str, full_name: str) -> dict:
    conn.execute(
        "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
        (email, password_hash, full_name)
    )
```

### 4. Add Email Verification

**Backend**:
```python
@app.post("/send-verification-email")
async def send_verification_email(email: str):
    # Generate token
    # Send email
    # Return success

@app.post("/verify-email")
async def verify_email(token: str):
    # Verify token
    # Mark user as verified
```

**Database**:
```sql
ALTER TABLE users ADD COLUMN verified BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN verification_token TEXT;
```

### 5. Add Password Reset

**Backend**:
```python
@app.post("/forgot-password")
async def forgot_password(email: str):
    # Generate reset token
    # Send reset link
    # Return success

@app.post("/reset-password")
async def reset_password(token: str, new_password: str):
    # Verify token
    # Hash new password
    # Update user
```

### 6. Change API Base URL

**Frontend**: `.env.local`
```env
VITE_API_URL=http://your-server-ip:8000
# or
VITE_API_URL=https://your-domain.com/api
```

### 7. Use HttpOnly Cookies (More Secure)

**Backend** (Replace token response):
```python
from fastapi.responses import JSONResponse

response = JSONResponse(
    {"email": user["email"]},
    status_code=200
)
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    secure=True,  # Only over HTTPS
    samesite="Lax"
)
return response
```

**Frontend** (Axios will auto-send cookies):
```javascript
const api = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true  // Send cookies with requests
})
```

## Adding Features

### 1. Add Two-Factor Authentication (2FA)

**Backend**:
```python
import pyotp

@app.post("/2fa/setup")
async def setup_2fa(user_id: int):
    secret = pyotp.random_base32()
    qr_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email, issuer_name='StockQuery'
    )
    return {"secret": secret, "qr_uri": qr_uri}

@app.post("/2fa/verify")
async def verify_2fa(user_id: int, token: str):
    totp = pyotp.TOTP(user_secret)
    if totp.verify(token):
        return {"success": True}
```

### 2. Add Rate Limiting

**Backend**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/login")
@limiter.limit("5/minute")  # Max 5 logins per minute
async def login(request: Request, auth: UserAuth):
    pass
```

### 3. Add User Roles & Permissions

**Database**:
```sql
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';
-- Roles: 'user', 'admin', 'moderator'
```

**Backend**:
```python
async def get_admin_user(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user or user["role"] != "admin":
        raise HTTPException(403, "Admin access required")
    return user

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(get_admin_user)):
    # Only admins can delete users
```

### 4. Add User Profile Page

**Backend**:
```python
@app.get("/profile")
async def get_profile(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(401, "Not authenticated")
    
    profile = await mcp_manager.call_tool("get_user_profile", {"user_id": user["user_id"]})
    return profile

@app.put("/profile")
async def update_profile(authorization: str = Header(None), data: dict = Body()):
    user = await get_current_user(authorization)
    if not user:
        raise HTTPException(401, "Not authenticated")
    
    result = await mcp_manager.call_tool("update_user_profile", {
        "user_id": user["user_id"],
        **data
    })
    return result
```

### 5. Add Social Login (Google/GitHub)

**Backend** (using google-auth library):
```python
from google.oauth2 import id_token
from google.auth.transport import requests

@app.post("/login/google")
async def login_google(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo['email']
        
        # Find or create user
        user = await mcp_manager.call_tool("get_or_create_user", {"email": email})
        
        # Issue JWT
        jwt_token = create_access_token({"user_id": user["id"], "email": email})
        return {"access_token": jwt_token, "token_type": "bearer"}
    except:
        raise HTTPException(401, "Invalid token")
```

## Testing & Debugging

### 1. Manual API Testing

**Using cURL**:
```bash
# Register
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Protected request
curl -X GET http://localhost:8000/history \
  -H "Authorization: Bearer <token>"
```

### 2. Frontend Testing

```javascript
// In browser console
// Check token
console.log(localStorage.getItem('token'))

// Make API call with token
fetch('http://localhost:8000/history', {
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
})
.then(r => r.json())
.then(console.log)
```

### 3. Database Inspection

```bash
# Connect to SQLite
sqlite3 mcp_server/inventory.db

# Check users
SELECT * FROM users;

# Check query history
SELECT * FROM query_history;

# Check password hash
SELECT email, password_hash FROM users WHERE email='test@example.com';
```

### 4. JWT Debugging

```python
# In backend
import jwt

token = "eyJ..."
payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
print(payload)  # See user_id, email, exp
```

### 5. Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| 422 Unprocessable Entity | Invalid request format | Check request body schema |
| 401 Unauthorized | Invalid/expired token | Re-login to get new token |
| 409 Conflict | Email already exists | Use different email |
| 500 Internal Server Error | Backend error | Check logs, verify JWT_SECRET |
| CORS Error | Frontend URL not in CORS | Update main.py CORS origins |

## Performance Optimization

### 1. Add Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_user_settings(user_id: int):
    # Cache user settings
    pass
```

### 2. Database Indexing

```sql
-- Add indexes for faster queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_query_history_user_id ON query_history(user_id);
CREATE INDEX idx_query_history_timestamp ON query_history(timestamp);
```

### 3. Connection Pooling

```python
from sqlalchemy import create_engine

engine = create_engine(
    'sqlite:///inventory.db',
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)
```

### 4. Async Database Queries

```python
import asyncpg

async def get_user_async(email: str):
    async with asyncpg.create_pool(DATABASE_URL) as pool:
        async with pool.acquire() as conn:
            user = await conn.fetchrow('SELECT * FROM users WHERE email=$1', email)
            return user
```

## Resources

- [FastAPI Authentication](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/)
- [Bcrypt Documentation](https://python-bcrypt.readthedocs.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Axios Documentation](https://axios-http.com/docs/intro)

## Questions?

- See AUTHENTICATION.md for complete API reference
- Check FLOWS.md for detailed flow diagrams
- Review backend/main.py for implementation examples
