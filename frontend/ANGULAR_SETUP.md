# Voyager Angular Frontend - Complete Setup Guide

## 📋 Overview

This guide covers the complete conversion from Streamlit to Angular/TypeScript for the Voyager application.

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── core/                      # Core services and guards
│   │   │   ├── services/
│   │   │   │   ├── auth.service.ts    # Authentication service
│   │   │   │   ├── api.service.ts     # HTTP API service
│   │   │   │   ├── athena.service.ts  # Athena-specific API calls
│   │   │   │   └── file-upload.service.ts
│   │   │   ├── guards/
│   │   │   │   ├── auth.guard.ts      # Route protection
│   │   │   │   └── admin.guard.ts     # Admin-only routes
│   │   │   ├── interceptors/
│   │   │   │   ├── auth.interceptor.ts # Add JWT to requests
│   │   │   │   └── error.interceptor.ts
│   │   │   └── models/
│   │   │       ├── user.model.ts
│   │   │       ├── query.model.ts
│   │   │       └── file.model.ts
│   │   │
│   │   ├── shared/                    # Shared components
│   │   │   ├── components/
│   │   │   │   ├── navbar/
│   │   │   │   ├── sidebar/
│   │   │   │   ├── alert/
│   │   │   │   └── file-uploader/
│   │   │   └── pipes/
│   │   │       ├── file-size.pipe.ts
│   │   │       └── time-ago.pipe.ts
│   │   │
│   │   ├── features/                  # Feature modules
│   │   │   ├── auth/
│   │   │   │   ├── login/
│   │   │   │   │   ├── login.component.ts
│   │   │   │   │   ├── login.component.html
│   │   │   │   │   └── login.component.scss
│   │   │   │   └── register/
│   │   │   │
│   │   │   ├── dashboard/
│   │   │   │   ├── dashboard.component.ts
│   │   │   │   ├── dashboard.component.html
│   │   │   │   └── dashboard.component.scss
│   │   │   │
│   │   │   ├── data-analysis/         # Replaces Streamlit
│   │   │   │   ├── data-analysis.component.ts
│   │   │   │   ├── data-analysis.component.html
│   │   │   │   ├── data-analysis.component.scss
│   │   │   │   ├── components/
│   │   │   │   │   ├── upload-section/
│   │   │   │   │   ├── query-section/
│   │   │   │   │   ├── results-display/
│   │   │   │   │   └── visualizations/
│   │   │   │   └── data-analysis-routing.module.ts
│   │   │   │
│   │   │   ├── athena/                # SQL Query Runner
│   │   │   │   ├── athena.component.ts
│   │   │   │   ├── athena.component.html
│   │   │   │   ├── athena.component.scss
│   │   │   │   ├── components/
│   │   │   │   │   ├── query-editor/
│   │   │   │   │   ├── database-browser/
│   │   │   │   │   ├── results-table/
│   │   │   │   │   └── admin-settings/
│   │   │   │   └── athena-routing.module.ts
│   │   │   │
│   │   │   └── admin/                 # Admin Panel
│   │   │       ├── admin.component.ts
│   │   │       ├── admin.component.html
│   │   │       ├── admin.component.scss
│   │   │       ├── components/
│   │   │       │   ├── user-management/
│   │   │       │   ├── system-settings/
│   │   │       │   └── statistics/
│   │   │       └── admin-routing.module.ts
│   │   │
│   │   ├── app.component.ts           # Root component
│   │   ├── app.component.html
│   │   ├── app.component.scss
│   │   ├── app.module.ts              # Root module
│   │   └── app-routing.module.ts      # App routing
│   │
│   ├── assets/                        # Static assets
│   │   ├── images/
│   │   └── icons/
│   │
│   ├── environments/                  # Environment configs
│   │   ├── environment.ts
│   │   └── environment.prod.ts
│   │
│   ├── styles/                        # Global styles
│   │   ├── _variables.scss
│   │   ├── _mixins.scss
│   │   └── _themes.scss
│   │
│   ├── index.html
│   ├── main.ts
│   ├── styles.scss
│   └── proxy.conf.json
│
├── angular.json
├── package.json
├── tsconfig.json
└── README.md
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm start
```

The app will open at `http://localhost:4200` and proxy API calls to `http://localhost:8000`

### 3. Build for Production

```bash
npm run build:prod
```

Output will be in `dist/voyager-frontend/`

## 📦 Key Dependencies

- **@angular/core**: Angular framework
- **@angular/material**: Material Design components
- **@angular/router**: Client-side routing
- **rxjs**: Reactive programming
- **plotly.js-dist-min**: Data visualizations
- **marked**: Markdown rendering (for AI responses)
- **highlight.js**: Code syntax highlighting

## 🔧 Configuration

### API Proxy Configuration (`src/proxy.conf.json`)

All API calls are proxied to the FastAPI backend during development:

```json
{
  "/api": { "target": "http://localhost:8000" },
  "/auth": { "target": "http://localhost:8000" },
  "/athena": { "target": "http://localhost:8000" }
}
```

### Environment Variables (`src/environments/environment.ts`)

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  appName: 'voyager',
  maxFileSize: 100 * 1024 * 1024, // 100MB
  maxFiles: 50
};
```

## 🎯 Features to Implement

### 1. **Authentication Module** (`features/auth/`)

#### Login Component
- Username/password form
- JWT token storage in localStorage
- Auto-redirect to dashboard
- Error handling

#### Register Component
- User registration form
- Password strength validation
- Email validation

### 2. **Dashboard** (`features/dashboard/`)

Central hub showing all available modules:
- Module cards with icons
- Role-based visibility (admin-only modules)
- Navigation to each feature

### 3. **Data Analysis Module** (`features/data-analysis/`)

Replaces Streamlit app with Angular components:

#### Upload Section
- Drag-and-drop file upload
- Multiple file support (up to 50)
- Progress indicators
- File list with metadata

#### Query Section
- Natural language query input
- Query history
- Intent detection display
- Suggested queries

#### Results Display
- Markdown-formatted AI responses
- Source citations
- Download options

#### Visualizations
- Plotly charts (bar, line, scatter, etc.)
- Interactive legends
- Export to PNG/SVG

### 4. **Athena Query Runner** (`features/athena/`)

SQL query interface for AWS Athena:

#### Query Editor
- SQL syntax highlighting
- Autocomplete
- Query history
- Keyboard shortcuts (Ctrl+Enter to execute)

#### Database Browser
- List databases
- List tables per database
- Click to insert table name

#### Results Table
- Paginated results
- Sortable columns
- CSV download (up to 100K rows)

#### Admin Settings (admin only)
- Configure max download rows
- Configure max display rows
- Real-time validation

### 5. **Admin Panel** (`features/admin/`)

User management and system settings:

#### User Management
- CRUD operations for users
- Password reset
- Role management
- User statistics

#### System Settings
- Athena configuration
- System-wide limits
- Audit logs viewer

## 🔐 Security Implementation

### Auth Guard (`core/guards/auth.guard.ts`)

```typescript
@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(): boolean {
    if (this.authService.isAuthenticated()) {
      return true;
    }
    this.router.navigate(['/login']);
    return false;
  }
}
```

### Auth Interceptor (`core/interceptors/auth.interceptor.ts`)

Automatically adds JWT token to all HTTP requests:

```typescript
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = this.authService.getToken();
    if (token) {
      req = req.clone({
        setHeaders: { Authorization: `Bearer ${token}` }
      });
    }
    return next.handle(req);
  }
}
```

### Error Interceptor

Handles 401 (unauthorized) responses globally:
- Auto-logout on token expiration
- Redirect to login
- Display error messages

## 🎨 Styling

### Angular Material Theme

Customize in `src/styles.scss`:

```scss
@use '@angular/material' as mat;

$voyager-primary: mat.define-palette(mat.$indigo-palette);
$voyager-accent: mat.define-palette(mat.$pink-palette, A200, A100, A400);
$voyager-warn: mat.define-palette(mat.$red-palette);

$voyager-theme: mat.define-light-theme((
  color: (
    primary: $voyager-primary,
    accent: $voyager-accent,
    warn: $voyager-warn,
  )
));

@include mat.all-component-themes($voyager-theme);
```

### Custom SCSS Variables

Define in `src/styles/_variables.scss`:

```scss
// Colors
$primary-color: #667eea;
$secondary-color: #764ba2;
$success-color: #48bb78;
$danger-color: #f56565;
$warning-color: #ed8936;

// Gradients
$gradient-primary: linear-gradient(135deg, $primary-color 0%, $secondary-color 100%);

// Spacing
$spacing-xs: 4px;
$spacing-sm: 8px;
$spacing-md: 16px;
$spacing-lg: 24px;
$spacing-xl: 32px;

// Shadows
$shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
$shadow-md: 0 4px 12px rgba(0, 0, 0, 0.15);
$shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.2);
```

## 🚦 Routing Configuration

### App Routing (`app-routing.module.ts`)

```typescript
const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [AuthGuard]
  },
  {
    path: 'data-analysis',
    loadChildren: () => import('./features/data-analysis/data-analysis.module')
      .then(m => m.DataAnalysisModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'athena',
    loadChildren: () => import('./features/athena/athena.module')
      .then(m => m.AthenaModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'admin',
    loadChildren: () => import('./features/admin/admin.module')
      .then(m => m.AdminModule),
    canActivate: [AuthGuard, AdminGuard]
  },
  { path: '**', redirectTo: '/dashboard' }
];
```

## 📡 API Service Pattern

### Generic API Service (`core/services/api.service.ts`)

```typescript
@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  // Generic GET
  get<T>(endpoint: string): Observable<T> {
    return this.http.get<T>(`${environment.apiUrl}${endpoint}`);
  }

  // Generic POST
  post<T>(endpoint: string, data: any): Observable<T> {
    return this.http.post<T>(`${environment.apiUrl}${endpoint}`, data);
  }

  // File upload with progress
  uploadFile(file: File): Observable<HttpEvent<any>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post('/upload', formData, {
      reportProgress: true,
      observe: 'events'
    });
  }
}
```

### Athena Service (`core/services/athena.service.ts`)

```typescript
@Injectable({ providedIn: 'root' })
export class AthenaService {
  constructor(private api: ApiService) {}

  executeQuery(query: string, database?: string): Observable<QueryResponse> {
    return this.api.post<QueryResponse>('/athena/query', { query, database });
  }

  downloadResults(query: string, database?: string): Observable<Blob> {
    return this.http.post('/athena/query/download',
      { query, database },
      { responseType: 'blob' }
    );
  }

  listDatabases(): Observable<DatabaseInfo> {
    return this.api.get<DatabaseInfo>('/athena/databases');
  }

  listTables(database: string): Observable<TableInfo> {
    return this.api.get<TableInfo>(`/athena/tables/${database}`);
  }

  // Admin only
  getSettings(): Observable<AthenaSettings> {
    return this.api.get<AthenaSettings>('/athena/admin/settings');
  }

  updateDownloadLimit(limit: number): Observable<any> {
    return this.api.put(`/athena/admin/settings/download-limit?limit=${limit}`, {});
  }
}
```

## 🧪 Testing

### Unit Tests

```bash
npm test
```

### E2E Tests

```bash
npm run e2e
```

## 📦 Production Deployment

### Build

```bash
npm run build:prod
```

### Serve with FastAPI

Update `backend/main.py` to serve the Angular dist folder:

```python
from fastapi.staticfiles import StaticFiles

# Serve Angular app
app.mount("/", StaticFiles(directory="frontend/dist/voyager-frontend", html=True), name="frontend")
```

### Docker Deployment

Create `frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build:prod

FROM nginx:alpine
COPY --from=build /app/dist/voyager-frontend /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🔄 Migration from Streamlit

### What Changes:
- ❌ **Remove**: `app.py` (Streamlit app)
- ❌ **Remove**: `static/` folder (old HTML files)
- ✅ **Add**: `frontend/` folder (Angular app)
- ✅ **Keep**: `backend/` folder (FastAPI - no changes needed)

### Benefits:
1. **Unified Frontend**: Single TypeScript codebase
2. **Better UX**: Faster page transitions, no page reloads
3. **Type Safety**: TypeScript catches errors at compile time
4. **Scalability**: Easier to add new features
5. **Modern Tooling**: Angular CLI, hot reload, debugging
6. **Mobile Responsive**: Better mobile experience
7. **SEO Friendly**: Can add server-side rendering later

## 📚 Learning Resources

- [Angular Documentation](https://angular.io/docs)
- [Angular Material](https://material.angular.io/)
- [RxJS](https://rxjs.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 4200
npx kill-port 4200
```

### Module Not Found
```bash
npm install
```

### API Connection Issues
- Check proxy.conf.json configuration
- Ensure FastAPI backend is running on port 8000
- Check browser console for CORS errors

## 📝 Next Steps

1. ✅ Install Node.js and npm
2. ✅ Run `npm install` in frontend directory
3. ✅ Implement core services (provided in this guide)
4. ✅ Create authentication components
5. ✅ Build dashboard
6. ✅ Implement data analysis module
7. ✅ Create Athena query runner
8. ✅ Add admin panel
9. ✅ Test thoroughly
10. ✅ Deploy to production

---

**Need Help?** Check the example components in `src/app/features/` for implementation patterns.

**Powered by Prodapt**
