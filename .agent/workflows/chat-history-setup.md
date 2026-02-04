---
description: How to set up and test the chat history feature
---

# Chat History Setup Workflow

This workflow guides you through setting up and testing the conversation history feature.

## Prerequisites

- MySQL server running on localhost:3306
- Python virtual environment activated
- Node.js and npm installed

## Step 1: Create MySQL Database

// turbo
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS History_of_conversations CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

Or run the SQL script:
```bash
mysql -u root -p < Backend/data/create_history_db.sql
```

## Step 2: Grant Permissions

```sql
GRANT ALL PRIVILEGES ON History_of_conversations.* TO 'rag_user'@'localhost';
FLUSH PRIVILEGES;
```

## Step 3: Install Backend Dependencies

// turbo
```bash
cd Backend
..\\.venv\\Scripts\\pip install aiomysql aiosqlite python-jose[cryptography] passlib[bcrypt] pydantic[email]
```

## Step 4: Start Backend Server

The database tables are automatically created on startup.

// turbo
```bash
cd Backend
..\.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 5: Start Frontend

// turbo
```bash
cd Frontend
npm run dev
```

## Step 6: Test the Feature

1. Open http://localhost:5173
2. Click "Sign In" button
3. Create a new account (any email/password)
4. Start chatting - conversations will be saved
5. Reload the page - your history persists
6. Click on sidebar items to load previous chats

## API Endpoints Reference

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Conversations
- `GET /api/conversations/sidebar` - Get sidebar list
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations/{id}` - Get conversation details
- `PUT /api/conversations/{id}/title` - Update title
- `DELETE /api/conversations/{id}` - Delete conversation

### Messages
- `GET /api/conversations/{id}/messages?page=1&page_size=30` - Get messages
- `POST /api/conversations/messages` - Send message

## Troubleshooting

### Database Connection Error
If you see "Could not initialize history DB", check:
1. MySQL is running
2. Database exists
3. Credentials in `.env` are correct

### SQLite Fallback
To use SQLite instead of MySQL (development):
```env
# In Backend/.env, comment out MySQL and use:
MYSQL_HISTORY_URL=sqlite+aiosqlite:///./Backend/data/conversations.db
```

### JWT Secret
For production, change the JWT_SECRET in `.env`:
```env
JWT_SECRET=your-very-long-random-secret-key-here
```
