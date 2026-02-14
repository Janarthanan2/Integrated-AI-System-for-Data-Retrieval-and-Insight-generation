# Integrated AI System for Data Retrieval & Insight Generation

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Android](https://img.shields.io/badge/Mobile-Android%20(Kotlin)-3DDC84)

A powerful **Virtual Data Analyst** that bridges the gap between raw data and decision-making. Ask questions in plain English, and the system securely retrieves relevant data from your databases, then uses advanced Large Language Models (LLMs) to generate actionable insights and dynamic visualizations — all through a modern chat interface available on **Web** and **Android**.

---

## 🚀 Key Features

- **🗣️ Natural Language Understanding** — Ask questions like *"What were the top 5 states by sales volume?"* instead of writing SQL.
- **📊 Dynamic Visualizations** — Automatically generates Line, Bar, Pie, and Scatter charts (via Recharts & ApexCharts) based on data context.
- **⚡ Direct Data Extraction** — Python-based extraction pipeline with NLP query parsing, fuzzy matching, and entity resolution — no Text-to-SQL hallucination risks.
- **🧠 RAG-Powered Insights** — Retrieval-Augmented Generation with models like `Mistral-7B` or `TinyLlama` to explain *why* trends are happening.
- **💬 Interactive Chat Interface** — Streaming responses, chat history persistence, conversation management, and optimistic UI updates.
- **🔐 Authentication & Security** — JWT-based auth, user isolation, parameterized queries, and role-based access control.
- **📱 Android App** — Native Kotlin Android client connecting to the same backend.
- **📝 Activity Logging** — Tracks and exports user activity logs to Excel (`.xlsx`) with backup support.
- **🔌 MCP Servers** — Model Context Protocol servers for RAG retrieval and SQLite data access.

---

## 🛠️ Tech Stack

### Backend
| Layer | Technologies |
|---|---|
| **Core** | FastAPI, Python 3.9+, Uvicorn |
| **Data Processing** | Pandas, NumPy, Scikit-learn |
| **AI / ML** | `sentence-transformers` (embeddings), `ctransformers` / `bitsandbytes` (quantized LLM inference), `transformers`, PyTorch |
| **NLP** | Custom `QueryExtractor` with fuzzy matching (`fuzzy_utils`), intent detection, entity resolution |
| **Database** | MySQL (via PyMySQL & SQLAlchemy), SQLite (conversations), async support via `aiomysql` / `aiosqlite` |
| **Auth** | JWT (`python-jose`), password hashing (`passlib[bcrypt]`), Pydantic email validation |
| **Document Retrieval** | `PyPDF2` for PDF parsing, embedding-based semantic search |
| **Logging** | Custom activity logger with Excel export (`openpyxl`) |

### Frontend (Web)
| Layer | Technologies |
|---|---|
| **Framework** | React 18 (Vite) |
| **UI Library** | Material UI v7 (`@mui/material`), Emotion, Bootstrap 5, React-Bootstrap |
| **Visualization** | Recharts, ApexCharts, MUI X Charts & Data Grid |
| **Markdown** | `react-markdown` with `remark-gfm` for rendering AI responses |
| **Icons** | Lucide React, MUI Icons |
| **State Management** | React Context (`AuthContext`, `ConversationsContext`) |

### Android App
| Layer | Technologies |
|---|---|
| **Language** | Kotlin |
| **Build System** | Gradle (Kotlin DSL) |
| **Networking** | HTTP client connecting to the FastAPI backend |

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.9 or higher
- Node.js & npm
- MySQL Server
- Android Studio (for mobile app development, optional)

### 1. Clone the Repository
```bash
git clone https://github.com/Janarthanan2/Integrated-AI-System-for-Data-Retrieval-and-Insight-generation.git
cd "Integrated-AI-System-for-Data-Retrieval-and-Insight-generation"
```

### 2. Backend Setup
```bash
cd Backend
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

**Environment Variables:** Create a `.env` file in the `Backend/` directory (see `.env.example`):
```ini
DATABASE_URL=mysql+pymysql://<user>:<password>@localhost:3306/<db_name>
DEFAULT_DB_LIMIT=50
SECRET_KEY=your_secret_key
```

### 3. Frontend Setup
```bash
cd ../Frontend
npm install
```

### 4. Android App Setup *(optional)*
1. Open the `AndroidApp/` directory in **Android Studio**.
2. Sync Gradle and let dependencies download.
3. Update the backend URL in the app's network configuration to point to your running server (use your machine's IP or an ngrok tunnel for device testing).
4. Build & run on an emulator or physical device.

---

## ▶️ Running the Application

### Start the Backend Server
From the `Backend/` directory:
```bash
uvicorn app.main:app --reload
```
> Server starts at `http://127.0.0.1:8000` — API docs available at `/docs`.

### Start the Frontend Client
From the `Frontend/` directory:
```bash
npm run dev
```
> Client starts at `http://localhost:5173`.

---

## 📂 Project Structure

```
├── Backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point & query processing
│   │   ├── query_extraction.py     # NLP intent & entity extraction
│   │   ├── generation.py           # LLM-powered insight generation (RAG)
│   │   ├── retrieval.py            # Document retrieval & embedding search
│   │   ├── analytics.py            # Data analysis & chart generation
│   │   ├── database.py             # Database connection & data fetching
│   │   ├── fuzzy_utils.py          # Fuzzy matching utilities
│   │   ├── security.py             # Security manager (JWT, RBAC)
│   │   ├── activity_logger.py      # User activity logging to Excel
│   │   ├── optimization.py         # Query & performance optimization
│   │   ├── utils.py                # Helper functions (summarize, trends)
│   │   ├── routers/                # API route handlers
│   │   │   ├── auth.py             #   └─ Authentication endpoints
│   │   │   └── conversations.py    #   └─ Chat history CRUD endpoints
│   │   ├── services/               # Business logic layer
│   │   │   ├── auth_service.py     #   └─ User registration & login
│   │   │   └── conversation_service.py  # └─ Conversation management
│   │   ├── db_models/              # SQLAlchemy ORM models
│   │   │   ├── base.py             #   └─ DB engine & session setup
│   │   │   ├── user.py             #   └─ User model
│   │   │   └── conversation.py     #   └─ Conversation & Message models
│   │   └── schemas/                # Pydantic request/response schemas
│   │       ├── auth.py             #   └─ Auth schemas
│   │       ├── conversation.py     #   └─ Conversation schemas
│   │       └── message.py          #   └─ Message schemas
│   ├── data/                       # Data files
│   │   ├── sales_data.csv          #   └─ Source business data
│   │   ├── sales_data.db           #   └─ SQLite copy for queries
│   │   └── embeddings_cache.pkl    #   └─ Pre-computed embeddings
│   ├── mcp_servers/                # Model Context Protocol servers
│   │   ├── rag_server/             #   └─ RAG retrieval MCP server
│   │   └── sqlite_server/          #   └─ SQLite data access MCP server
│   ├── requirements.txt            # Python dependencies
│   └── .env.example                # Environment variable template
│
├── Frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main app component & routing
│   │   ├── main.jsx                # React entry point
│   │   ├── index.css               # Global styles & design system
│   │   ├── components/
│   │   │   ├── LandingPage.jsx     #   └─ Homepage / hero section
│   │   │   ├── AuthModal.jsx       #   └─ Sign In / Sign Up modal
│   │   │   ├── ChatInput.jsx       #   └─ Auto-expanding message input
│   │   │   ├── ChatHistory.jsx     #   └─ Message history renderer
│   │   │   ├── AnalyticsCharts.jsx #   └─ Chart rendering components
│   │   │   ├── Sidebar.jsx         #   └─ Conversation sidebar
│   │   │   └── SettingsModal.jsx   #   └─ User settings panel
│   │   ├── api/
│   │   │   ├── config.js           #   └─ API base URL configuration
│   │   │   ├── auth.js             #   └─ Auth API calls
│   │   │   └── conversations.js    #   └─ Conversation API calls
│   │   └── contexts/
│   │       ├── AuthContext.jsx      #   └─ Authentication state
│   │       └── ConversationsContext.jsx  # └─ Conversation state
│   ├── package.json
│   └── vite.config.js
│
├── AndroidApp/                     # Native Android client (Kotlin)
│   ├── app/                        # App module (source, resources, manifests)
│   ├── build.gradle.kts            # Root build configuration
│   └── settings.gradle.kts         # Gradle settings
│
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/process` | Process a natural language query (streaming SSE response) |
| `GET` | `/models` | List available LLM models |
| `POST` | `/switch-model` | Switch the active LLM model |
| `GET` | `/health` | Health check |
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and receive JWT token |
| `GET` | `/conversations/` | List user conversations |
| `POST` | `/conversations/` | Create a new conversation |
| `GET` | `/conversations/{id}/messages` | Get messages for a conversation |
| `GET` | `/admin/logs` | View activity logs (JSON) |
| `GET` | `/admin/logs/download` | Download activity logs (Excel) |
| `POST` | `/admin/logs/backup` | Create a backup of activity logs |

> Full interactive API docs available at `http://localhost:8000/docs` when the server is running.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is developed as part of an academic main project (Phase II).
