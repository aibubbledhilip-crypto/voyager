# 🚀 Voyager - Application Startup Guide

## Quick Start

### **Easiest Way - Use the Startup Script**

```bash
cd /home/user/voyager
./start.sh
```

That's it! The script will:
- ✅ Create virtual environment (if needed)
- ✅ Install all dependencies
- ✅ Start FastAPI backend (port 8000)
- ✅ Start Streamlit frontend (port 8501)
- ✅ Show you all access URLs

### **To Stop the Application**

```bash
./stop.sh
```

---

## Manual Startup (If you prefer)

### **Step 1: Install Dependencies**

```bash
cd /home/user/voyager
pip install -r requirements.txt
```

### **Step 2: Start FastAPI Backend**

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Keep this terminal open.

### **Step 3: Start Streamlit Frontend (New Terminal)**

Open a new terminal and run:

```bash
cd /home/user/voyager
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 🌐 Access URLs

Once both servers are running, you can access:

| Module | URL | Description |
|--------|-----|-------------|
| **Main Dashboard** | http://localhost:8000/static/dashboard.html | Entry point with all modules |
| **SQL Athena Runner** | http://localhost:8000/static/athena.html | Execute SQL queries, download CSVs |
| **Data Analysis** | http://localhost:8501 | RAG-powered data analysis (Streamlit) |
| **Admin Panel** | http://localhost:8000/static/admin.html | User management (admin only) |
| **API Documentation** | http://localhost:8000/docs | FastAPI Swagger docs |

---

## 🔑 Default Login Credentials

```
Username: admin
Password: admin123
```

**⚠️ Important:** Change these credentials in production!

---

## 🔧 Configuration

### **Environment Variables**

Create a `.env` file in the project root:

```bash
# FastAPI Settings
HOST=0.0.0.0
PORT=8000

# OpenAI API Key (for RAG queries)
OPENAI_API_KEY=your_openai_api_key_here

# AWS Athena Configuration
ATHENA_DATABASE=your_database_name
ATHENA_OUTPUT_LOCATION=s3://your-bucket/athena-results/
AWS_REGION=us-east-1
ATHENA_WORKGROUP=primary

# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Database (SQLite by default)
DATABASE_URL=sqlite:///./data/app.db
```

---

## 📊 Available Modules

### 1. **📊 Intelligent RAG Data Analysis**
- Upload CSV/Excel files (up to 50+)
- Ask questions in natural language
- AI-powered insights and visualizations
- Automatic intent detection (ML-based)

### 2. **🔍 SQL Athena Query Runner** ⭐ NEW
- Execute SQL queries on AWS Athena
- Download results as CSV (up to 100K rows default)
- Browse databases and tables
- **Admin controls**: Configure download limits (1K - 1M rows)
- Comprehensive SQL injection protection
- Rate limiting (10 queries/minute per user)

### 3. **⚙️ Admin Dashboard** (Admin Only)
- User management (CRUD operations)
- Create/edit/delete users
- Reset passwords
- View system statistics
- Configure Athena limits

---

## 🔒 Security Features

### SQL Athena Module Security:
- ✅ Multi-layer SQL injection prevention
- ✅ Dangerous keyword blocking (DROP, DELETE, etc.)
- ✅ Pattern-based attack detection
- ✅ Identifier sanitization
- ✅ Rate limiting per user (10 queries/min)
- ✅ Comprehensive audit logging
- ✅ Query size limits (10,000 chars max)
- ✅ Only SELECT, SHOW, DESCRIBE allowed

### Authentication:
- ✅ JWT token-based authentication
- ✅ Bcrypt password hashing
- ✅ Role-based access control (admin vs user)
- ✅ Session sharing between apps
- ✅ Auto-logout on token expiration

---

## 📝 Logs

Logs are saved in the `logs/` directory:
- `logs/backend.log` - FastAPI backend logs
- `logs/streamlit.log` - Streamlit frontend logs

**View logs in real-time:**

```bash
# Backend logs
tail -f logs/backend.log

# Streamlit logs
tail -f logs/streamlit.log
```

---

## 🐛 Troubleshooting

### **Port already in use:**

```bash
# Kill processes on port 8000
lsof -ti:8000 | xargs kill -9

# Kill processes on port 8501
lsof -ti:8501 | xargs kill -9
```

### **Module not found errors:**

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### **Database not initialized:**

```bash
# Initialize the database
python -c "from backend.database import init_db; init_db()"
```

### **Can't see Athena module on dashboard:**

1. Clear browser cache: `Ctrl + Shift + Delete`
2. Hard refresh: `Ctrl + F5` or `Ctrl + Shift + R`
3. Restart the backend server

### **Session not shared between apps:**

Make sure you're using the latest version (session sharing was added in commit `bbcaf8a`):

```bash
git pull origin claude/intelligent-rag-data-analysis-011CUv9UryAcKtA4cwaCmPR3
```

---

## 🔄 Updates & Maintenance

### **Pull Latest Changes:**

```bash
git pull origin claude/intelligent-rag-data-analysis-011CUv9UryAcKtA4cwaCmPR3
```

### **Update Dependencies:**

```bash
pip install -r requirements.txt --upgrade
```

### **Rebuild Database:**

```bash
rm data/app.db
python -c "from backend.database import init_db; init_db()"
```

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Security Documentation**: See `SECURITY_ATHENA.md`
- **Git Repository**: Check commit history for changelog

---

## 💡 Tips

1. **First Time Setup**: Run `./start.sh` - it handles everything automatically
2. **Development**: Use `--reload` flag with uvicorn for auto-restart on code changes
3. **Production**: Remove `--reload` and set proper environment variables
4. **AWS Athena**: Configure AWS credentials before using the Athena module
5. **Admin Settings**: Only admins can see/modify Athena download limits

---

## 🆘 Need Help?

- Check logs in `logs/` directory
- Review API documentation at `/docs`
- Check `SECURITY_ATHENA.md` for security details
- Review commit messages for recent changes

---

**Powered by Prodapt**
