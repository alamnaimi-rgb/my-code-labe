# 🚀 MyCodeLab — Full Professional Version

**Personal/College Coding Platform** - Save Questions, Write Code, Execute, Manage Files, Take Notes, and Practice!

## 🎯 Features

- 📚 **Question Management** - Save programming questions with difficulty, language, and tags
- 💻 **Professional Code Editor** - Monaco Editor with syntax highlighting, multiple files, tabs
- ▶️ **Code Execution** - Run C, C++, Python, Java, JavaScript, SQL in sandboxed containers
- 📁 **File Manager** - Create folders, organize code, manage files
- 🔗 **Question ↔ Solution Connection** - Link questions with code solutions
- 📝 **Notes System** - Add concepts, important points, and common mistakes
- 🔍 **Global Search** - Search questions, files, and notes
- ⭐ **Favorites** - Mark important questions and files
- 🗑️ **Trash & Recovery** - Safe deletion with recovery option
- 📊 **Coding Statistics** - Track progress with charts and metrics
- 🧪 **Test Cases** - Run code against predefined test cases
- 🤖 **AI Features** (Future) - Code explanation, debugging, hints
- 🌙 **Dark/Light Mode** - Theme switching with persistence
- 📱 **Mobile Responsive** - Works on all devices
- 🔐 **Security** - Password hashing, session management, CSRF protection
- ☁️ **Online Database** - PostgreSQL for production, SQLite for development

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, JavaScript, Monaco Editor
- **Backend**: Python Flask
- **Database**: SQLite (Dev) / PostgreSQL (Prod)
- **Authentication**: Flask sessions with secure password hashing
- **Code Execution**: Docker containers (Sandboxed)
- **Deployment**: Free-tier cloud hosting
- **Version Control**: Git + GitHub

## 📂 Project Structure

```
MyCodeLab/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── config.py             # Configuration settings
├── README.md             # This file
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore file
│
├── database/
│   ├── models.py         # Database models
│   ├── init_db.py        # Database initialization
│   └── mycodlab.db       # SQLite database (dev)
│
├── auth/
│   ├── routes.py         # Authentication routes (login, register, logout)
│   ├── forms.py          # Authentication forms
│   └── utils.py          # Password hashing, session management
│
├── questions/
│   ├── routes.py         # Question CRUD routes
│   ├── forms.py          # Question forms
│   └── utils.py          # Question utilities
│
├── editor/
│   ├── routes.py         # Code editor routes
│   ├── forms.py          # Editor forms
│   └── utils.py          # File operations
│
├── executor/
│   ├── routes.py         # Code execution routes
│   ├── sandbox.py        # Sandboxed execution
│   └── languages.py      # Language support (C, C++, Python, Java, JS, SQL)
│
├── search/
│   ├── routes.py         # Search routes
│   └── utils.py          # Search utilities
│
├── static/
│   ├── css/
│   │   ├── style.css           # Main styles
│   │   ├── dashboard.css       # Dashboard styles
│   │   ├── editor.css          # Editor styles
│   │   └── responsive.css      # Mobile responsive styles
│   │
│   ├── js/
│   │   ├── app.js              # Main app logic
│   │   ├── editor.js           # Monaco editor setup
│   │   ├── darkmode.js         # Dark/Light mode toggle
│   │   ├── search.js           # Search functionality
│   │   └── api.js              # API calls
│   │
│   └── images/
│       └── logo.png
│
├── templates/
│   ├── base.html               # Base template with navbar, sidebar
│   ├── index.html              # Dashboard
│   ├── auth/
│   │   ├── login.html          # Login page
│   │   ├── register.html       # Register page
│   │   └── forgot_password.html# Forgot password
│   │
│   ├── questions/
│   │   ├── list.html           # Questions list
│   │   ├── view.html           # Single question
│   │   ├── add.html            # Add question
│   │   ├── edit.html           # Edit question
│   │   └── search_results.html # Search results
│   │
│   ├── editor/
│   │   ├── index.html          # Code editor main page
│   │   ├── file_manager.html   # File manager
│   │   └── file_explorer.html  # File browser
│   │
│   ├── notes/
│   │   ├── list.html           # Notes list
│   │   ├── view.html           # View note
│   │   └── add.html            # Add note
│   │
│   ├── profile/
│   │   ├── settings.html       # User settings
│   │   ├── stats.html          # Coding statistics
│   │   └── favorites.html      # Favorites
│   │
│   ├── trash.html              # Trash page
│   └── errors/
│       ├── 404.html            # 404 error
│       └── 500.html            # 500 error
│
└── tests/
    ├── test_auth.py            # Authentication tests
    ├── test_questions.py       # Questions tests
    ├── test_editor.py          # Editor tests
    └── test_executor.py        # Executor tests
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git
- Docker (for code execution sandbox)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/alamnaimi-rgb/my-code-labe.git
   cd my-code-labe
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python database/init_db.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Open in browser**
   ```
   http://localhost:5000
   ```

## 📊 Development Phases

### Phase 1 ✅ - Foundation
- [x] Flask setup
- [x] Database models
- [x] Dashboard layout
- [x] Questions CRUD

### Phase 2 ✅ - Code System
- [x] Code editor (Monaco)
- [x] Save/Load code
- [x] File manager
- [x] Folder management
- [x] Question ↔ Code connection

### Phase 3 ✅ - Professional UI
- [x] Sidebar navigation
- [x] Navbar with search
- [x] Dark/Light mode
- [x] Responsive design
- [x] Professional styling

### Phase 4 ✅ - Code Execution
- [x] C execution
- [x] C++ execution
- [x] Python execution
- [x] Java execution
- [x] JavaScript execution
- [x] SQL execution
- [x] Sandboxed execution
- [x] Test cases support
- [x] Error handling

### Phase 5 ✅ - User System
- [x] User registration
- [x] Login/Logout
- [x] Password hashing
- [x] Session management
- [x] User-specific data
- [x] Forgot password
- [x] Change password

### Phase 6 ✅ - Advanced
- [x] Notes system
- [x] Favorites management
- [x] Tags system
- [x] Trash/Recovery
- [x] Coding statistics
- [x] Activity tracking
- [x] Practice mode

### Phase 7 - AI (Future)
- [ ] AI Explain
- [ ] AI Debug
- [ ] AI Hints
- [ ] Question Generator
- [ ] Code Review

### Phase 8 - Production
- [ ] PostgreSQL migration
- [ ] Security hardening
- [ ] Performance optimization
- [ ] Deployment setup
- [ ] CI/CD pipeline

## 🔐 Security Features

- ✅ Password hashing (bcrypt)
- ✅ Secure session management
- ✅ CSRF protection
- ✅ Input validation
- ✅ SQL injection protection (ORM)
- ✅ XSS protection
- ✅ File upload validation
- ✅ Rate limiting
- ✅ Secure code execution (Docker sandbox)
- ✅ Environment variables for secrets
- ✅ Debug mode OFF in production

## 🌐 Deployment

### Free Hosting Options
- Heroku (with PostgreSQL)
- Railway
- Render
- Replit
- PythonAnywhere

### Docker Deployment
```bash
docker build -t mycodlab .
docker run -p 5000:5000 mycodlab
```

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/logout` - Logout user
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password/<token>` - Reset password

### Questions
- `GET /questions` - List all questions
- `POST /questions` - Create question
- `GET /questions/<id>` - Get question
- `PUT /questions/<id>` - Update question
- `DELETE /questions/<id>` - Delete question
- `POST /questions/<id>/favorite` - Add to favorites

### Code Editor
- `GET /editor` - Editor page
- `POST /editor/save` - Save file
- `GET /editor/file/<id>` - Load file
- `PUT /editor/file/<id>` - Update file
- `DELETE /editor/file/<id>` - Delete file
- `POST /editor/folder` - Create folder

### Code Execution
- `POST /executor/run` - Execute code
- `POST /executor/test` - Run test cases

### Search
- `GET /search?q=query` - Global search

### Notes
- `GET /notes` - List notes
- `POST /notes` - Create note
- `GET /notes/<id>` - Get note
- `PUT /notes/<id>` - Update note
- `DELETE /notes/<id>` - Delete note

### Profile
- `GET /profile` - User profile
- `GET /profile/stats` - Coding statistics
- `GET /profile/settings` - Settings
- `PUT /profile/settings` - Update settings

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

Run specific test:
```bash
pytest tests/test_auth.py
```

## 📝 Database Schema

### Users
```sql
id, username, email, password_hash, created_at, updated_at, theme
```

### Questions
```sql
id, user_id, title, description, language, difficulty, topic, tags, created_at, updated_at
```

### Code Files
```sql
id, user_id, question_id, filename, filepath, content, language, created_at, updated_at
```

### Folders
```sql
id, user_id, name, parent_id, created_at, updated_at
```

### Notes
```sql
id, user_id, question_id, content, created_at, updated_at
```

### Test Cases
```sql
id, question_id, input, expected_output, created_at
```

### Favorites
```sql
id, user_id, question_id, created_at
```

### Trash
```sql
id, user_id, item_type, item_id, deleted_at
```

### Activity Log
```sql
id, user_id, action, details, created_at
```

## 🤝 Contributing

Contributions are welcome! Please follow the coding standards and create pull requests.

## 📄 License

MIT License - Free to use for personal and commercial projects.

## 👨‍💻 Author

**Alam Naimi** - Personal Coding Platform

## 📞 Support

For issues or questions, please create an issue in the GitHub repository.

---

**Built with ❤️ for programmers and students**
