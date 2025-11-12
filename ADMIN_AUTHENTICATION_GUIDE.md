# Admin Authentication & User Management Guide

## 🔐 Overview

Voyager now includes a comprehensive authentication system with full admin controls for user management. Admins can create users, modify credentials, control permissions, and monitor system usage.

---

## 🚀 Quick Start

### 1. Start the Server

```bash
cd /home/user/voyager
python backend/main.py
```

The server will automatically create a default admin user on first run.

### 2. Default Admin Credentials

```
Username: admin
Password: admin123
```

**⚠️ IMPORTANT:** Change the admin password immediately after first login!

### 3. Access the System

- **Login Page:** `http://localhost:8000/static/login.html`
- **Admin Dashboard:** `http://localhost:8000/static/admin.html`
- **Register:** `http://localhost:8000/static/register.html`

---

## 👥 User Roles

### Regular User
- Upload and analyze files
- Run queries
- View own data
- Update own profile

### Administrator (Super User)
- All regular user permissions
- Create/delete users
- Modify user credentials
- Promote/demote users to admin
- Activate/deactivate accounts
- View system statistics
- Monitor user activity

---

## 🎯 Admin Features

### 1. User Management

**Create New Users:**
- Set username, email, password
- Assign admin privileges
- Set active/inactive status

**Edit Users:**
- Update email and full name
- Reset passwords
- Toggle admin privileges
- Activate/deactivate accounts

**Delete Users:**
- Permanently remove users
- Cannot delete yourself
- Deletes all associated data

### 2. Dashboard Statistics

- **Total Users** - Number of registered users
- **Active Users** - Currently active accounts
- **Total Files** - Files uploaded across all users
- **Storage Used** - Total storage consumption

### 3. User Overview

View comprehensive user information:
- Username and email
- Role (Admin/User)
- Status (Active/Inactive)
- File count
- Storage usage
- Account creation date

---

## 📋 API Endpoints

### Authentication Endpoints

#### Login
```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Register
```http
POST /auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure123",
  "full_name": "John Doe"
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

#### Update Profile
```http
PUT /auth/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "New Name",
  "email": "newemail@example.com",
  "password": "newpassword"
}
```

---

### Admin Endpoints (Require Admin Role)

#### List All Users
```http
GET /auth/users
Authorization: Bearer <admin-token>
```

**Response:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Administrator",
    "is_active": true,
    "is_admin": true,
    "api_key": "sk_..."
  }
]
```

#### Create User (Admin)
```http
POST /auth/users?is_admin=false
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure123",
  "full_name": "Jane Smith"
}
```

#### Get User by ID
```http
GET /auth/users/{user_id}
Authorization: Bearer <admin-token>
```

#### Update User (Admin)
```http
PUT /auth/users/{user_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "full_name": "Updated Name",
  "password": "newpassword",
  "is_admin": true,
  "is_active": true
}
```

**Features:**
- Update any user field
- Reset passwords
- Promote/demote admin status
- Activate/deactivate accounts
- Cannot demote yourself

#### Delete User
```http
DELETE /auth/users/{user_id}
Authorization: Bearer <admin-token>
```

**Safety:**
- Cannot delete yourself
- Confirmation required
- Permanently removes user and data

#### Toggle User Active Status
```http
PUT /auth/users/{user_id}/toggle-active
Authorization: Bearer <admin-token>
```

#### Reset User Password
```http
POST /auth/users/{user_id}/reset-password?new_password=newpass123
Authorization: Bearer <admin-token>
```

#### Get User Statistics
```http
GET /auth/users/{user_id}/stats
Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "user_id": 2,
  "username": "john",
  "email": "john@example.com",
  "is_admin": false,
  "is_active": true,
  "total_files": 15,
  "total_queries": 234,
  "storage_used": "45.32 MB",
  "created_at": "2024-01-15T10:30:00"
}
```

#### Admin Dashboard
```http
GET /auth/admin/dashboard
Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "total_users": 10,
  "active_users": 8,
  "admin_users": 2,
  "total_files": 150,
  "total_queries": 3456,
  "storage_used": "523.45 MB"
}
```

---

## 🔑 Authentication Methods

### 1. JWT Tokens (Recommended for UI)

**How it works:**
1. User logs in with username/password
2. Server returns JWT token
3. Client includes token in Authorization header
4. Token expires after 24 hours

**Usage:**
```javascript
// Login
const response = await fetch('/auth/token', {
    method: 'POST',
    body: new FormData({
        username: 'admin',
        password: 'admin123'
    })
});
const { access_token } = await response.json();

// Use token
const userData = await fetch('/auth/me', {
    headers: {
        'Authorization': `Bearer ${access_token}`
    }
});
```

### 2. API Keys (Recommended for Scripts)

**Generate API Key:**
```http
POST /auth/me/regenerate-api-key
Authorization: Bearer <token>
```

**Use API Key:**
```bash
curl -H "X-API-Key: sk_abc123..." http://localhost:8000/auth/me
```

---

## 🛡️ Security Features

### Password Security
- Bcrypt hashing with salt
- Minimum 6 characters required
- Passwords never stored in plain text

### Token Security
- JWT tokens with HS256 algorithm
- 24-hour expiration
- Secure secret key (configurable)

### Admin Protection
- Cannot delete yourself
- Cannot remove your own admin privileges
- Confirmation required for destructive actions

### Session Management
- Token-based authentication
- Automatic logout on token expiration
- Refresh token support (optional)

---

## 📱 Frontend Pages

### Login Page (`/static/login.html`)
- Clean, modern design
- Form validation
- Error handling
- Remember credentials
- Redirect to appropriate dashboard

### Register Page (`/static/register.html`)
- User registration form
- Password strength indicator
- Email validation
- Automatic login after registration

### Admin Dashboard (`/static/admin.html`)
- System statistics overview
- User management table
- Create/edit/delete users
- Modal dialogs for forms
- Real-time updates
- Responsive design

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
# Security
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# Database
DATABASE_URL=sqlite:///./data/app.db  # Or use PostgreSQL: postgresql://user:pass@localhost/dbname
```

### Change Default Admin Credentials

Edit `backend/auth.py`:

```python
def init_admin_user(db: Session):
    """Initialize default admin user if none exists"""
    admin = db.query(User).filter(User.is_admin == True).first()
    if not admin:
        admin = create_user(
            db=db,
            username="your_admin_username",  # Change this
            email="your_admin@email.com",    # Change this
            password="your_secure_password", # Change this
            full_name="Administrator",
            is_admin=True
        )
```

---

## 🧪 Testing

### Test Admin Features

```bash
# Start server
python backend/main.py

# In another terminal, test endpoints
# Login as admin
curl -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=admin123"

# Get token from response, then:
TOKEN="your_token_here"

# List users
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/auth/users

# Get dashboard stats
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/auth/admin/dashboard

# Create user
curl -X POST http://localhost:8000/auth/users?is_admin=false \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "test123"
  }'
```

---

## 📊 Database Schema

### User Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    api_key VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tenant Table

```sql
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    owner_id INTEGER REFERENCES users(id),
    storage_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🚨 Common Issues & Solutions

### Issue: "Not authenticated"

**Solution:**
- Check if token is valid
- Token may have expired (24h default)
- Re-login to get new token

### Issue: "Not enough permissions"

**Solution:**
- Verify user has admin role
- Check `is_admin` field in user table
- Admin privileges may have been revoked

### Issue: "User already exists"

**Solution:**
- Username or email is taken
- Choose different username/email
- Check existing users in admin dashboard

### Issue: Cannot delete user

**Solution:**
- Cannot delete yourself
- Ensure user exists
- Check admin permissions

---

## 🔒 Best Practices

### 1. Change Default Credentials
```bash
# Immediately after installation
# 1. Login as admin
# 2. Go to profile
# 3. Change password
```

### 2. Use Strong Passwords
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Don't reuse passwords

### 3. Limit Admin Accounts
- Only create admin users when necessary
- Regular users have sufficient permissions for most tasks
- Audit admin accounts periodically

### 4. Monitor User Activity
- Check dashboard regularly
- Review user statistics
- Disable inactive accounts

### 5. Backup Database
```bash
# SQLite
cp data/app.db data/app.db.backup

# PostgreSQL
pg_dump dbname > backup.sql
```

---

## 🔄 Workflow Examples

### Creating a New Team Member

1. **Admin logs in** → `/static/login.html`
2. **Opens admin dashboard** → `/static/admin.html`
3. **Clicks "Create New User"**
4. **Fills in details:**
   - Username: `john_doe`
   - Email: `john@company.com`
   - Password: (temporary password)
   - Role: User (not admin)
5. **User receives credentials** (via secure channel)
6. **User logs in** and changes password

### Promoting User to Admin

1. **Admin opens dashboard**
2. **Finds user in table**
3. **Clicks "Edit"**
4. **Checks "Administrator" checkbox**
5. **Saves changes**
6. **User now has admin privileges**

### Resetting User Password

1. **Admin opens dashboard**
2. **Finds user in table**
3. **Clicks "Edit"**
4. **Enters new password**
5. **Saves changes**
6. **Communicates new password to user securely**

### Deactivating User Account

1. **Admin opens dashboard**
2. **Finds user in table**
3. **Clicks "Edit"**
4. **Unchecks "Active" checkbox**
5. **Saves changes**
6. **User can no longer login**

---

## 📞 Support & Troubleshooting

### Check Logs

```bash
# Server logs show authentication attempts
# Look for errors in console output
python backend/main.py
```

### Database Inspection

```bash
# SQLite
sqlite3 data/app.db
sqlite> SELECT * FROM users;
sqlite> .quit
```

### Reset Admin Password (Emergency)

```python
# In Python console
from backend.database import SessionLocal, User
from backend.auth import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
admin.hashed_password = get_password_hash('new_password')
db.commit()
print("Password reset successful")
```

---

## ✅ Summary

Voyager's authentication system provides:

✅ **Secure Authentication** - JWT tokens + API keys
✅ **Admin Controls** - Full user management
✅ **Modern UI** - Beautiful login and admin dashboard
✅ **Role-Based Access** - Admin and regular user roles
✅ **Password Management** - Reset, update, hash
✅ **User Statistics** - Monitor activity and storage
✅ **API First** - RESTful endpoints for all operations
✅ **Production Ready** - Security best practices

---

## 🎯 Next Steps

1. **Change default admin password**
2. **Create user accounts for team**
3. **Configure environment variables**
4. **Set up proper database (PostgreSQL for production)**
5. **Enable HTTPS in production**
6. **Set up backup procedures**

---

**Enjoy secure, enterprise-grade authentication with Voyager! 🚀**
