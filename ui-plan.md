# Vue.js Client Implementation Plan

> **Reference the original client code at `cloudgene3/src/main/html/webapp/` when designing and building UI components and structure to achieve full feature parity.** For each view and component, consult the corresponding CanJS/Stache component in the original app to ensure all functionality, form controls, and UI behaviours are replicated.

## Tech Stack

| Concern | Choice | Reason |
|---|---|---|
| Framework | **Vue 3** (Composition API) | Modern, well-supported, good ecosystem |
| Router | **Vue Router 4** | Official, SPA routing with guards |
| State | **Pinia** | Lightweight, Vue 3 native replacement for Vuex |
| HTTP | **Axios** | Interceptors make auth headers easy |
| UI | **Bootstrap 5** | Matches original app; familiar to users |
| Icons | **Font Awesome 6** | Same as original |
| Charts | **Chart.js** | Modern replacement for Morris.js |
| Build | **Vite** | Fast dev server, simple config |
| WebSockets | **Native browser API** | Thin wrapper for job status updates |

The client will live in a `frontend/` directory at the project root and be served as static files by Django in production.

---

## Directory Structure

```
frontend/
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/index.js
│   ├── stores/
│   │   ├── auth.js          # Current user, token, login/logout
│   │   ├── jobs.js          # Job list, active job state
│   │   └── server.js        # Navbar items, server settings
│   ├── api/
│   │   ├── client.js        # Axios instance with auth interceptor
│   │   ├── auth.js
│   │   ├── jobs.js
│   │   ├── workflows.js
│   │   ├── users.js
│   │   └── admin.js
│   ├── views/
│   │   ├── public/
│   │   │   ├── HomeView.vue
│   │   │   ├── LoginView.vue
│   │   │   ├── RegisterView.vue
│   │   │   ├── ActivateView.vue
│   │   │   ├── PasswordResetView.vue
│   │   │   ├── PasswordRecoveryView.vue
│   │   │   ├── ProfileView.vue
│   │   │   ├── JobListView.vue
│   │   │   ├── JobDetailView.vue
│   │   │   ├── WorkflowSubmitView.vue
│   │   │   └── StaticPageView.vue
│   │   └── admin/
│   │       ├── AdminDashboardView.vue
│   │       ├── AdminJobsView.vue
│   │       ├── AdminUsersView.vue
│   │       ├── AdminWorkflowsView.vue
│   │       ├── AdminWorkflowSettingsView.vue
│   │       └── settings/
│   │           ├── GeneralSettingsView.vue
│   │           ├── NextflowSettingsView.vue
│   │           ├── MailSettingsView.vue
│   │           ├── TemplateEditorView.vue
│   │           └── LogsView.vue
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppNavbar.vue        # Dynamic navbar from API
│   │   │   ├── AppFooter.vue        # HTML template from API
│   │   │   ├── AdminSidebar.vue
│   │   │   └── AdminLayout.vue
│   │   ├── jobs/
│   │   │   ├── JobStatusBadge.vue
│   │   │   ├── JobListTable.vue
│   │   │   ├── JobLogTab.vue
│   │   │   ├── JobStepsTab.vue      # Step progress, accordion
│   │   │   └── JobResultsTab.vue    # Download links, share
│   │   ├── workflows/
│   │   │   ├── WorkflowCard.vue
│   │   │   └── form/
│   │   │       ├── DynamicForm.vue  # Renders inputs from YAML params
│   │   │       ├── TextInput.vue
│   │   │       ├── FileInput.vue    # Upload with progress dialog
│   │   │       ├── SelectInput.vue
│   │   │       ├── CheckboxInput.vue
│   │   │       └── TermsInput.vue
│   │   ├── admin/
│   │   │   ├── StatsCard.vue
│   │   │   ├── JobsChart.vue        # Chart.js area chart
│   │   │   └── UserRow.vue
│   │   └── common/
│   │       ├── LoadingSpinner.vue
│   │       ├── AlertMessage.vue
│   │       ├── ConfirmDialog.vue
│   │       └── Pagination.vue
├── public/
│   └── index.html
├── package.json
└── vite.config.js
```

---

## Routes

```
/                         → HomeView (public, HTML from templates API)
/login                    → LoginView
/register                 → RegisterView
/activate/:key            → ActivateView
/reset-password           → PasswordResetView
/recover/:token           → PasswordRecoveryView
/profile                  → ProfileView (auth required)
/jobs                     → JobListView (auth required)
/jobs/:id                 → JobDetailView (auth required, tabs: logs/steps/results)
/run/:workflowId          → WorkflowSubmitView (auth required)
/pages/:slug              → StaticPageView (HTML from templates API)

/admin                    → AdminDashboardView (admin required)
/admin/jobs               → AdminJobsView
/admin/users              → AdminUsersView
/admin/workflows          → AdminWorkflowsView
/admin/workflows/:id      → AdminWorkflowSettingsView
/admin/settings/general   → GeneralSettingsView
/admin/settings/nextflow  → NextflowSettingsView
/admin/settings/mail      → MailSettingsView
/admin/settings/templates → TemplateEditorView
/admin/settings/logs      → LogsView
```

Navigation guards will redirect unauthenticated users to `/login` and non-admins away from `/admin/*`.

---

## Implementation Phases

### Phase 1 — Foundation
- Vite + Vue 3 project scaffold in `frontend/`
- Axios API client with auth token interceptor
- Pinia `auth` store (login, logout, token persistence via `localStorage`)
- Vue Router with auth guards
- `AppNavbar` loading items from `/api/admin/navbar-items/`
- `AppFooter` rendering HTML from templates API
- Login, Register, Activate, and Password Reset views

### Phase 2 — Job Submission & Monitoring
- `WorkflowSubmitView` with `DynamicForm` parsing workflow parameters (text, file, select, checkbox, radio, textarea, terms inputs)
- File upload with progress tracking dialog
- `JobListView` with pagination and status filtering
- `JobDetailView` with three tabs:
  - **Logs** — raw job log output
  - **Steps** — accordion-style step progress
  - **Results** — file list with download/share links
- WebSocket integration for real-time job status updates on the detail view

### Phase 3 — Admin Interface
- `AdminLayout` with sidebar navigation
- `AdminDashboardView` with stats cards and Chart.js area chart (jobs over time)
- `AdminJobsView` — all jobs, filterable by status, cancel action
- `AdminUsersView` — paginated user list with group management, delete
- `AdminWorkflowsView` + `AdminWorkflowSettingsView` — enable/disable workflows, manage group access, install from GitHub/URL
- Settings pages (general, nextflow, mail, template editor, logs viewer)

### Phase 4 — Polish & Integration
- Django serves `frontend/dist/` as static files; catch-all URL routes to `index.html`
- Responsive layout testing
- Error handling, empty states, loading skeletons
- Profile page (view/edit user details, copy API token)
- Static content pages (`/pages/:slug`)

---

## Key Design Decisions

1. **Dynamic navbar**: `AppNavbar` fetches `NavbarItem` list from API on app load; admin-only items are shown only to admin users.
2. **Auth persistence**: Token stored in `localStorage`, injected by Axios interceptor on every request. On 401 response, the interceptor clears auth state and redirects to `/login`.
3. **Dynamic form rendering**: `DynamicForm` maps workflow parameter types (from `/api/workflows/:id/`) to matching input components. This is the most complex part of the submission flow.
4. **WebSocket job monitor**: The job detail view opens a WebSocket to `ws://.../ws/jobs/:id/` and listens for step/status updates, closing cleanly on unmount.
5. **Admin vs user layout**: Admin routes use `AdminLayout` (sidebar); public routes use `AppNavbar` + `AppFooter`. Both are separate layout components, not nested inside each other.
