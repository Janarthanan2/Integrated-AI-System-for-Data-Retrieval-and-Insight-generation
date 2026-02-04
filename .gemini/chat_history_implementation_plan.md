# Chat History Implementation Plan

## Overview
Implement a full-featured chat history system with MySQL persistence, JWT authentication, optimistic UI, and artifact storage for charts.

---

## 📦 Phase 1: Database Setup

### 1.1 Create MySQL Database for Conversations
```sql
-- Database: History_of_conversations (or use existing business_ai)
CREATE DATABASE IF NOT EXISTS History_of_conversations;
USE History_of_conversations;
```

### 1.2 Create Tables

#### Users Table
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Conversations Table
```sql
CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    last_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_updated (user_id, updated_at DESC)
);
```

#### Messages Table
```sql
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    conversation_id VARCHAR(36) NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation_created (conversation_id, created_at)
);
```

#### Artifacts Table (for charts)
```sql
CREATE TABLE artifacts (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    message_id VARCHAR(36) NOT NULL,
    conversation_id VARCHAR(36) NOT NULL,
    type ENUM('chart', 'table', 'code') NOT NULL,
    chart_type VARCHAR(50),
    spec JSON,
    data_snapshot JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);
```

---

## 📦 Phase 2: Backend Implementation

### 2.1 New Files to Create

| File | Purpose |
|------|---------|
| `Backend/app/models/conversation.py` | SQLAlchemy models for conversations, messages, artifacts |
| `Backend/app/models/user.py` | User model with password hashing |
| `Backend/app/routers/auth.py` | JWT authentication endpoints |
| `Backend/app/routers/conversations.py` | Conversation CRUD endpoints |
| `Backend/app/routers/messages.py` | Message endpoints with pagination |
| `Backend/app/routers/artifacts.py` | Artifact storage/retrieval |
| `Backend/app/services/conversation_service.py` | Business logic for conversations |
| `Backend/app/middleware/auth.py` | JWT verification middleware |
| `Backend/app/schemas/` | Pydantic schemas for request/response |

### 2.2 Dependencies to Add
```txt
# Add to requirements.txt
aiomysql          # Async MySQL driver
python-jose[cryptography]  # JWT tokens
passlib[bcrypt]   # Password hashing
pydantic[email]   # Email validation
```

### 2.3 API Endpoints

#### Auth Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| GET | `/api/auth/me` | Get current user |

#### Conversation Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations/sidebar` | Get user's conversations (cached) |
| POST | `/api/conversations` | Create new conversation |
| GET | `/api/conversations/{id}` | Get conversation details |
| DELETE | `/api/conversations/{id}` | Delete conversation |
| PUT | `/api/conversations/{id}/title` | Update title |

#### Message Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations/{id}/messages` | Get messages (paginated) |
| POST | `/api/messages` | Send message + get AI response |

#### Artifact Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations/{id}/artifacts` | Get all artifacts |
| GET | `/api/artifacts/{id}` | Get specific artifact |

---

## 📦 Phase 3: Frontend Implementation

### 3.1 New Components to Create

| Component | Purpose |
|-----------|---------|
| `Sidebar.jsx` | Conversation list with search |
| `ConversationItem.jsx` | Single conversation in sidebar |
| `AuthContext.jsx` | JWT auth state management |
| `LoginModal.jsx` | Login/Register form |
| `useConversations.js` | Hook for conversation management |
| `useAuth.js` | Hook for authentication |
| `api/conversations.js` | API client for conversations |
| `api/auth.js` | API client for auth |

### 3.2 State Management
```javascript
// App State Structure
{
  auth: { user, token, isAuthenticated },
  conversations: {
    list: [...],      // Sidebar items
    activeId: null,   // Current conversation
    cache: {},        // Message cache by conversation ID
  },
  ui: {
    sidebarOpen: true,
    isLoading: false,
  }
}
```

### 3.3 Optimistic UI Flow
1. User sends message → Immediately render in chat
2. Show typing indicator
3. Send to backend async
4. Update sidebar with new `last_message`
5. Stream AI response tokens
6. Save artifact if chart generated

---

## 📦 Phase 4: Implementation Order

### Step 1: Backend Models & Database (30 min)
- [ ] Create `models/` directory with SQLAlchemy models
- [ ] Create database migration script
- [ ] Test database connection

### Step 2: Auth System (45 min)
- [ ] Implement user registration/login
- [ ] JWT token generation/verification
- [ ] Auth middleware for protected routes

### Step 3: Conversation API (1 hr)
- [ ] CRUD endpoints for conversations
- [ ] Sidebar API with caching
- [ ] Message pagination

### Step 4: Integrate with Existing Query Flow (45 min)
- [ ] Modify `/query` to save messages
- [ ] Store chart artifacts
- [ ] Update conversation metadata

### Step 5: Frontend Sidebar (1 hr)
- [ ] Create Sidebar component
- [ ] Implement conversation switching
- [ ] Add new chat button

### Step 6: Auth UI (45 min)
- [ ] Login/Register modal
- [ ] Protected routes
- [ ] Persist auth token

### Step 7: Polish & Optimization (30 min)
- [ ] Optimistic UI updates
- [ ] Error handling
- [ ] Loading states

---

## 🔧 Configuration Updates

### Backend `.env`
```env
# Add these
MYSQL_HISTORY_URL=mysql+aiomysql://rag_user:Janamax%40004@localhost:3306/History_of_conversations
JWT_SECRET=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

### Frontend Environment
```javascript
// src/config.js
export const API_URL = "http://127.0.0.1:8000/api";
export const AUTH_TOKEN_KEY = "nova_auth_token";
```

---

## 🚀 Quick Start Commands

```bash
# 1. Create MySQL database
mysql -u root -p -e "CREATE DATABASE History_of_conversations;"

# 2. Install new dependencies
cd Backend
pip install aiomysql python-jose passlib pydantic[email]

# 3. Run database migrations (after creating tables)
python -m app.init_db

# 4. Start backend
uvicorn app.main:app --reload
```

---

## Notes

- **User Isolation**: Every query MUST filter by `user_id` from JWT
- **Caching**: Use in-memory dict initially, Redis later if needed
- **Pagination**: Default 30 messages, load more on scroll
- **Charts**: Store as JSON spec, render client-side with Chart.js
