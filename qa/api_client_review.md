# API Client Review - Format Discrepancies Analysis

**Date:** 2026-05-19  
**Reviewer:** Claude Code  
**Purpose:** Identify and fix content-type mismatches between frontend and backend

## Issues Identified

### 🚨 CRITICAL: Content-Type Conflicts

**Problem**: Default client sets `application/json` but some endpoints need `multipart/form-data`

**Current State:**
```javascript
// frontend/src/api/client.js
const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },  // ❌ Default conflicts with FormData
})

// frontend/src/api/jobs.js  
export const submitJob = (data) =>
  client.post('/jobs/', data, { headers: { 'Content-Type': 'multipart/form-data' } })  // ✅ Correct override
```

**Impact:** 
- ✅ Job submission works (has override)
- ⚠️ Future FormData endpoints may break if they don't override headers
- ⚠️ Axios automatic Content-Type detection is disabled

## API Endpoints Analysis

### ✅ auth.js - All JSON (Correct)
- `login(username, password)` - JSON ✓
- `logout()` - No body ✓ 
- `register(data)` - JSON ✓
- `requestPasswordReset(email)` - JSON ✓
- `confirmPasswordReset(token, password)` - JSON ✓

### ✅ users.js - All JSON (Correct) 
- `updateUser(id, data)` - JSON ✓
- `createGroup(data)` - JSON ✓
- All GET/DELETE requests - No body issues ✓

### ✅ workflows.js - All GET (Correct)
- All endpoints are GET requests ✓
- No body/content-type issues ✓

### ✅ admin.js - All JSON (Correct)
- `updateServerSettings(data)` - JSON ✓
- `updateTemplate(id, data)` - JSON ✓  
- `updateWorkflowSettings(workflowId, data)` - JSON ✓
- All other endpoints are GET requests ✓

### ⚠️ jobs.js - FormData Override (Fixed but brittle)
- `submitJob(data)` - Uses FormData override ✓
- **Risk**: Manual override required for FormData endpoints

## File Upload Analysis

### ✅ File Handling (Correct)
- `FileInput.vue` properly emits File objects ✓
- `DynamicForm.vue` appends Files to FormData ✓
- Backend `JobSubmissionSerializer` handles FormData ✓

## Recommendations

### 1. Fix Default Content-Type Header
**Problem**: Forcing `application/json` prevents automatic content-type detection

**Solution**: Let Axios auto-detect content type
```javascript
// Remove forced Content-Type header
const client = axios.create({
  baseURL: '/api',
  // headers: { 'Content-Type': 'application/json' },  // Remove this line
})
```

### 2. Remove Manual FormData Override  
**Problem**: Manual header override is brittle and unnecessary

**Solution**: Remove explicit header from jobs.js
```javascript
// Remove manual Content-Type override
export const submitJob = (data) =>
  client.post('/jobs/', data)  // Axios will auto-detect FormData
```

### 3. Add Content-Type Detection Logic
**Alternative**: Smart content-type detection
```javascript
client.interceptors.request.use((config) => {
  // Auto-detect FormData and remove Content-Type header to let axios handle it
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  } else if (!config.headers['Content-Type']) {
    config.headers['Content-Type'] = 'application/json'
  }
  
  const token = localStorage.getItem('cg_token')
  if (token) {
    config.headers['Authorization'] = `Token ${token}`
  }
  return config
})
```

## Backend Compatibility Check

### ✅ Django REST Framework Default Parsers
- JSONParser handles `application/json` ✓
- MultiPartParser handles `multipart/form-data` ✓  
- FormParser handles `application/x-www-form-urlencoded` ✓

### ✅ Custom Job Submission Handler
- `JobSubmissionSerializer.to_internal_value()` handles FormData ✓
- Backward compatible with JSON ✓

## Testing Recommendations

### Test Cases Needed:
1. **JSON submission** - auth, users, admin endpoints
2. **FormData submission** - job submission with files  
3. **FormData submission** - job submission without files
4. **Mixed content** - ensure no cross-contamination

### Selenium Test Updates:
```javascript
// Test different content types
test('json_api_calls', () => {
  // Test auth, admin calls work with JSON
})

test('formdata_api_calls', () => {
  // Test job submission works with FormData
})
```

## Security Considerations

### ✅ CSRF Protection  
- Django CSRF middleware enabled ✓
- Token authentication used ✓
- No CSRF token needed for API endpoints with Token auth ✓

### ✅ File Upload Security
- No file upload endpoints outside of job submission ✓
- Job submission requires authentication ✓  
- Files handled through FormData properly ✓

## Conclusion

**Current Status**: ✅ Working but fragile
**Risk Level**: 🟡 Medium (could break with changes)
**Recommended Fix**: Remove forced Content-Type and let Axios auto-detect

**Priority Actions**:
1. Remove default `Content-Type: application/json` from client.js  
2. Remove manual FormData override from jobs.js
3. Test all endpoints to ensure compatibility
4. Add automated tests for different content types