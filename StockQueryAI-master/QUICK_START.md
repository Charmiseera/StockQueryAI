# Quick Start Guide - Authentication System

## 5-Minute Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- pip and npm

### Step 1: Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Install Frontend Dependencies
```bash
cd frontend
npm install
```

### Step 3: Configure Environment

Create `.env` in project root:
```bash
NEBIUS_API_KEY=your-api-key-here
JWT_SECRET=your-secret-key-change-this-in-production
ELEVENLABS_API_KEY=optional
ELEVENLABS_VOICE_ID=optional
```

Create `frontend/.env.local`:
```bash
VITE_API_URL=http://localhost:8000
```

### Step 4: Start Services

**Terminal 1 - MCP Server:**
```bash
cd mcp_server
python server.py
```

**Terminal 2 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 5: Access Application

Open: http://localhost:5173

You'll see a login/register modal. Create an account and start using the app!

## Authentication Features

✓ **Register** - Create account with email & password
✓ **Login** - Secure authentication with JWT
✓ **Protected Queries** - Your queries are saved to your account
✓ **Query History** - View your previous questions and answers
✓ **Auto-Login** - Token persists across sessions
✓ **Input Validation** - Email format and password strength checks

## Key Files Modified/Created

- `frontend/src/services/api.js` - Centralized API client with JWT support
- `frontend/src/components/AuthModal.jsx` - Enhanced login/register UI
- `frontend/src/App.jsx` - Integrated authentication flow
- `backend/requirements.txt` - Added PyJWT and passlib
- `backend/main.py` - Already has endpoints (no changes needed)
- `mcp_server/server.py` - Already has user DB functions (no changes needed)
- `AUTHENTICATION.md` - Complete documentation

## Testing Your Setup

1. **Register a new account**
   - Email: test@example.com
   - Password: password123

2. **Login**
   - Use same credentials

3. **Query**
   - Ask: "Show me all products"
   - Check localStorage → Token is stored

4. **Check History**
   - Click "History" tab to see saved queries

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | Make sure all 3 services are running |
| "Email already exists" | Use a different email to register |
| "Invalid email or password" | Check exact email/password |
| Token errors | Check JWT_SECRET matches in .env |
| CORS errors | Verify VITE_API_URL is correct |

## Next Steps

1. Read full [AUTHENTICATION.md](./AUTHENTICATION.md) for complete guide
2. Customize styling in AuthModal.jsx
3. Add more validation rules as needed
4. Set up production environment variables
5. Deploy to your server

## Files Structure

```
StockQueryAI-master/
├── backend/
│   ├── main.py                 (FastAPI with auth endpoints)
│   └── requirements.txt        (Added PyJWT, passlib)
├── frontend/
│   ├── src/
│   │   ├── services/
│   │   │   └── api.js          (NEW - Centralized API client)
│   │   ├── components/
│   │   │   └── AuthModal.jsx   (UPDATED - Enhanced UI)
│   │   └── App.jsx             (UPDATED - Auth flow)
│   └── .env.example            (NEW - Frontend config)
├── mcp_server/
│   └── server.py               (Already has user functions)
├── AUTHENTICATION.md           (NEW - Full documentation)
└── QUICK_START.md             (NEW - This file)
```

## Support

See [AUTHENTICATION.md](./AUTHENTICATION.md) for detailed troubleshooting and API documentation.
