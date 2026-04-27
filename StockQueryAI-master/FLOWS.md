# Authentication Flow Diagrams

## 1. Registration Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ User fills register form
       │ (name, email, password)
       ↓
┌──────────────────────────┐
│  AuthModal.jsx           │
│ - Validate inputs        │
│ - Check email format     │
│ - Check pwd length >= 6  │
│ - Confirm pwd matches    │
└──────┬───────────────────┘
       │ Form valid?
       ├─ NO → Show error ──┐
       │                    │
       │ YES                │
       ↓                    │
┌──────────────────────────┐│
│  POST /register          ││
│  {email, password}       ││
└──────┬───────────────────┘│
       │                    │
       ↓                    │
┌──────────────────────────┐│
│  backend/main.py         ││
│ - Hash pwd with bcrypt   ││
└──────┬───────────────────┘│
       │                    │
       ↓                    │
┌──────────────────────────┐│
│  mcp_server/server.py    ││
│ - Call register_user()   ││
│ - INSERT into users      ││
│ - Check email unique     ││
└──────┬───────────────────┘│
       │                    │
       ├─ Email exists?     │
       │  └─ YES → Error ───┼─→ Show "Email already exists"
       │                    │
       │  NO                │
       ↓                    │
┌──────────────────────────┐│
│  {success: true}         ││
└──────┬───────────────────┘│
       │                    │
       ↓                    │
┌──────────────────────────┐│
│  Frontend                ││
│ - Show success msg       ││
│ - Switch to login        ││
│ - Auto-clear form        ││
└──────────────────────────┘│
                            │
                            └─→ Show error message
```

## 2. Login Flow

```
┌──────────────────────────┐
│  User enters email & pwd │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  AuthModal.jsx           │
│ - Validate email format  │
│ - Validate pwd not empty │
└──────┬───────────────────┘
       │
       ├─ Invalid? → Show error ──┐
       │                          │
       │ Valid                    │
       ↓                          │
┌──────────────────────────┐     │
│  POST /login             │     │
│  {email, password}       │     │
└──────┬───────────────────┘     │
       │                          │
       ↓                          │
┌──────────────────────────┐     │
│  backend/main.py         │     │
│ 1. Call authenticate_user│     │
└──────┬───────────────────┘     │
       │                          │
       ↓                          │
┌──────────────────────────┐     │
│  mcp_server/server.py    │     │
│ - SELECT from users      │     │
│ - Return password_hash   │     │
└──────┬───────────────────┘     │
       │                          │
       ├─ User not found?         │
       │  └─ YES → Error ─────────┼─→ Show "Invalid credentials"
       │                          │
       │ User found              │
       ↓                          │
┌──────────────────────────┐     │
│  backend/main.py         │     │
│ 2. Verify password hash  │     │
│    (bcrypt.verify)       │     │
└──────┬───────────────────┘     │
       │                          │
       ├─ Hash mismatch?          │
       │  └─ YES → Error ─────────┼─→ Show "Invalid credentials"
       │                          │
       │ Hash matches             │
       ↓                          │
┌──────────────────────────┐     │
│  backend/main.py         │     │
│ 3. Create JWT token      │     │
│    - Encode user_id      │     │
│    - Set exp: +7 days    │     │
│    - Sign with JWT_SECRET│     │
└──────┬───────────────────┘     │
       │                          │
       ↓                          │
┌──────────────────────────┐     │
│  Response:               │     │
│ {                        │     │
│  access_token: "xyz...", │     │
│  token_type: "bearer",   │     │
│  email: "user@..."       │     │
│ }                        │     │
└──────┬───────────────────┘     │
       │                          │
       ↓                          │
┌──────────────────────────┐     │
│  Frontend:               │     │
│ - Store token in storage │     │
│ - Store email in storage │     │
│ - Close auth modal       │     │
│ - Fetch query history    │     │
│ - Load main app          │     │
└──────────────────────────┘     │
                                  │
                                  └─→ Show error message
```

## 3. Protected Query Request Flow

```
┌──────────────────────────┐
│  User submits query      │
│  "Show all products"     │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  App.jsx                 │
│ - Set loading state      │
│ - Add to messages        │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  services/api.js         │
│ Interceptor:             │
│ 1. Check localStorage    │
│ 2. Get token             │
│ 3. Add header:           │
│    Authorization:        │
│    Bearer <token>        │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  POST /query             │
│  {question: "..."}       │
│  Headers:                │
│    Authorization:        │
│    Bearer eyJ...         │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  backend/main.py         │
│ 1. Parse Authorization   │
│ 2. Extract token         │
│ 3. Call get_current_user │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  backend/main.py         │
│  get_current_user():     │
│ 1. Decode JWT            │
│ 2. Verify signature      │
│ 3. Check expiration      │
└──────┬───────────────────┘
       │
       ├─ Token invalid?      ┐
       │  └─ YES → 401 error  │
       │                      ↓
       │              Frontend Interceptor:
       │              1. Remove token
       │              2. Clear localStorage
       │              3. Redirect to login
       │              4. Show auth modal
       │
       │ Token valid
       ↓
┌──────────────────────────┐
│  backend/main.py         │
│ 1. Execute query         │
│ 2. Get LLM response      │
│ 3. MCP calls tools       │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  mcp_server/server.py    │
│ 1. Execute tool          │
│ 2. Save to query_history │
│    with user_id          │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Response:               │
│ {                        │
│  answer: "Found...",     │
│  tool_used: "...",       │
│  data: [...]             │
│ }                        │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Frontend:               │
│ 1. Add AI response       │
│ 2. Display in chat       │
│ 3. Update history        │
│ 4. Show data table       │
└──────────────────────────┘
```

## 4. Token Expiration Handling Flow

```
┌──────────────────────────┐
│  Stored JWT expires      │
│  (7 days from creation)  │
└──────┬───────────────────┘
       │
       ↓ (when user tries to query)
┌──────────────────────────┐
│  api.js interceptor      │
│  Adds Authorization:     │
│  Bearer <expired_token>  │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  backend/main.py         │
│  jwt.decode()            │
│  Checks expiration       │
└──────┬───────────────────┘
       │
       ├─ Token expired → jwt.ExpiredSignatureError
       │
       ↓
┌──────────────────────────┐
│  get_current_user()      │
│  Returns None            │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Endpoint handler        │
│  Returns 401 error       │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Response Interceptor    │
│  Detects 401 status      │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Frontend cleanup:       │
│ 1. Remove token          │
│ 2. Remove email          │
│ 3. Clear user state      │
│ 4. localStorage.clear()  │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  window.location = '/'   │
│  Redirect to home        │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  App reloads             │
│  No token found          │
│  Show auth modal         │
│  User must login again   │
└──────────────────────────┘
```

## 5. Session Persistence Flow

```
┌─────────────────────────────────────────┐
│  User closes and reopens browser        │
└──────┬────────────────────────────────┬─┘
       │                                │
       ↓ (first page load)              │
┌──────────────────────────┐            │
│  App.jsx useEffect       │            │
│  Runs on mount           │            │
└──────┬───────────────────┘            │
       │                                │
       ├─ Check localStorage ◄──────────┼──┐
       │  - Get token                   │  │
       │  - Get email                   │  │
       │                                │  │
       ├─ Token and email found?        │  │
       │                                │  │
       │  YES                           │  │
       ↓                                │  │
┌──────────────────────────┐            │  │
│  User state set          │            │  │
│ {email, token}           │            │  │
└──────┬───────────────────┘            │  │
       │                                │  │
       ↓                                │  │
┌──────────────────────────┐            │  │
│  Fetch query history     │            │  │
│  Call GET /history       │            │  │
│  Add Authorization:      │            │  │
│  Bearer <token>          │            │  │
└──────┬───────────────────┘            │  │
       │                                │  │
       ↓                                │  │
┌──────────────────────────┐            │  │
│  Load previous queries   │            │  │
│  Restore conversation    │            │  │
│  Skip auth modal         │            │  │
│  Go to main app          │            │  │
└──────────────────────────┘            │  │
                                        │  │
       NO token/email found             │  │
       ├─────────────────────────────────┘  │
       ↓                                     │
┌──────────────────────────┐                │
│  Show auth modal         │                │
│  User must login again   │                │
└──────────────────────────┘                │
                                            │
                  └────────────────────────┘
```

## 6. Database State Changes

```
┌─────────────────────────────────────────────────────┐
│  Before Registration                                │
├─────────────────────────────────────────────────────┤
│ users table (empty)                                 │
│ query_history table (empty)                         │
└─────────────────────────────────────────────────────┘
        │
        ↓ User registers: john@example.com, password123
┌─────────────────────────────────────────────────────┐
│  After Registration                                 │
├─────────────────────────────────────────────────────┤
│ users:                                              │
│ ┌──────────────────────────────────────────────┐   │
│ │ id │ email              │ password_hash      │   │
│ ├──────────────────────────────────────────────┤   │
│ │ 1  │ john@example.com   │ $2b$10$xxx...     │   │
│ │    │                    │ (bcrypt hash)      │   │
│ └──────────────────────────────────────────────┘   │
│                                                     │
│ query_history: (empty)                              │
└─────────────────────────────────────────────────────┘
        │
        ↓ User logs in and submits query
        ↓ Query: "Show all Dairy products"
┌─────────────────────────────────────────────────────┐
│  After Query Submission                             │
├─────────────────────────────────────────────────────┤
│ users: (unchanged)                                  │
│                                                     │
│ query_history:                                      │
│ ┌──────────────────────────────────────────────┐   │
│ │ id │ user_id │ question │ answer │ tool_used │   │
│ ├──────────────────────────────────────────────┤   │
│ │ 1  │ 1       │ "Show... │ "Here  │ search_  │   │
│ │    │ (john)  │ all...   │ are... │ inventory│   │
│ └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
        │
        ↓ User logs out
        ↓ Database unchanged (data persists)
┌─────────────────────────────────────────────────────┐
│  After Logout                                       │
├─────────────────────────────────────────────────────┤
│ users: (unchanged - john still exists)              │
│ query_history: (unchanged - queries preserved)      │
└─────────────────────────────────────────────────────┘
        │
        ↓ User logs back in with same credentials
        ↓ Previous queries are automatically loaded
┌─────────────────────────────────────────────────────┐
│  After Re-login                                     │
├─────────────────────────────────────────────────────┤
│ Frontend calls: GET /history with user_id=1        │
│ Returns all queries where user_id=1                 │
│ Conversation is restored to state before logout     │
└─────────────────────────────────────────────────────┘
```

## Token Lifecycle Timeline

```
Time 0:
├─ User logs in
├─ JWT created with exp: now + 7 days
├─ Token stored in localStorage
├─ Displayed as: ███████████████ (7 days)
└─ User can query freely

Time 1 day:
├─ Token still valid
├─ Displayed as: ███████████     (6 days remaining)
├─ All queries work normally
└─ Backend verifies token: ✓ Valid

Time 3 days:
├─ Token still valid
├─ Displayed as: █████████       (4 days remaining)
├─ All queries work normally
└─ Backend verifies token: ✓ Valid

Time 7 days:
├─ Token expires
├─ Displayed as:                 (0 days remaining)
├─ Next query attempt fails
├─ Backend verifies token: ✗ Expired
├─ Error response: 401 Unauthorized
├─ Frontend clears token
├─ Frontend redirects to login
└─ User must login again for new token

Time 7 days + 1 second:
├─ localStorage empty
├─ App shows auth modal
├─ User enters credentials
├─ Backend issues new token
├─ New expiration: 7 days from now
└─ User can query again
```

## Security Flow

```
┌─────────────────┐
│  User Password  │ (Sent via HTTPS only in production)
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│  backend/main.py                        │
│  pwd_context.hash(password)             │
│  ├─ Generate random salt                │
│ ├─ Apply bcrypt algorithm               │
│ ├─ Round: 10                            │
│ └─ Output: $2b$10$xxx...                │
└────────┬────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│  mcp_server/server.py                   │
│  INSERT password_hash into users        │
│  (NOT plain password)                   │
└────────┬────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│  SQLite Database                        │
│  ┌───────────────────────────────────┐  │
│  │ email: john@example.com           │  │
│  │ password_hash:                    │  │
│  │ $2b$10$abcdefghijklmnopqrstuv...  │  │
│  │ (cannot reverse to get password)  │  │
│  └───────────────────────────────────┘  │
└────────┬────────────────────────────────┘
         │
         ↓ (on login)
         │
┌─────────────────────────────────────────┐
│  User submits password again            │
│  (NOT stored in DB)                     │
└────────┬────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│  backend/main.py                        │
│  pwd_context.verify(                    │
│    submitted_password,                  │
│    stored_hash_from_db                  │
│  )                                      │
│  ├─ Apply same hash to submitted pwd    │
│  ├─ Compare with stored hash            │
│  └─ Return True/False (never False→pwd) │
└────────┬────────────────────────────────┘
         │
         ├─ Match: ✓ Create JWT → Login
         └─ No match: ✗ Deny Access
```
