# Admin API Documentation

This document describes the Admin OAuth2 mock flow and admin bookings CRUD endpoints implemented in the BackendAPI.

## Overview

The Admin API provides:
1. **Mock OAuth2 Authorization Code Flow** for admin panel authentication
2. **Admin Identity Endpoint** to retrieve admin user info from JWT
3. **Admin Bookings CRUD** with full create, read, update, delete operations
4. **Admin Scope Enforcement** via JWT token validation

All admin endpoints require a valid JWT token with `scope: admin`.

---

## Authentication Flow

### 1. OAuth2 Authorization Code Flow (Mock)

#### Step 1: Authorization Request

**Endpoint:** `GET /api/v1/oauth/authorize`

**Query Parameters:**
- `response_type` (required): Must be `code`
- `client_id` (required): Registered OAuth client ID
- `redirect_uri` (required): Callback URL for your admin panel
- `scope` (optional): Requested scopes (default: `admin`)
- `state` (optional): Opaque value for CSRF protection

**Example Request:**
```
GET /api/v1/oauth/authorize?response_type=code&client_id=mock-google-client&redirect_uri=https://admin.example.com/callback&state=xyz123
```

**Response:**
- `302 Found` - Redirects to `redirect_uri` with authorization code
- Redirect URL: `https://admin.example.com/callback?code=<authorization_code>&state=xyz123`

**Errors:**
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Unknown or invalid client_id

---

#### Step 2: Token Exchange

**Endpoint:** `POST /api/v1/oauth/token`

**Request Body:**
```json
{
  "grant_type": "authorization_code",
  "code": "<authorization_code_from_step1>",
  "redirect_uri": "https://admin.example.com/callback",
  "client_id": "mock-google-client",
  "client_secret": "mock-google-secret"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "scope": "admin"
}
```

**Errors:**
- `400 Bad Request` - Invalid grant_type or redirect_uri mismatch
- `401 Unauthorized` - Invalid client credentials or expired/invalid code

**Token Claims:**
The issued JWT contains:
```json
{
  "sub": "admin",
  "scope": "admin",
  "client_id": "mock-google-client",
  "role": "admin",
  "aud": "admin-panel",
  "iat": 1234567890,
  "nbf": 1234567890,
  "exp": 1234571490
}
```

---

### 2. Admin Identity Endpoint

**Endpoint:** `GET /api/v1/admin/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "sub": "admin",
  "scope": "admin",
  "iat": 1234567890,
  "exp": 1234571490,
  "nbf": 1234567890,
  "client_id": "mock-google-client"
}
```

**Errors:**
- `401 Unauthorized` - Missing, invalid, or expired token
- `401 Unauthorized` - Token lacks `admin` scope

---

## Admin Bookings API

All booking endpoints require an admin-scoped JWT token.

### 1. List All Bookings

**Endpoint:** `GET /api/v1/bookings`

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `limit` (optional, default: 20, max: 200): Number of records to return
- `offset` (optional, default: 0): Number of records to skip

**Response:**
```json
[
  {
    "id": 123456789,
    "userId": 987654321,
    "roomId": 456789123,
    "status": "booked",
    "checkIn": "2024-01-15",
    "checkOut": "2024-01-20"
  }
]
```

**Errors:**
- `401 Unauthorized` - Missing or invalid admin token

---

### 2. Create Booking

**Endpoint:** `POST /api/v1/bookings`

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Request Body:**
```json
{
  "userId": 987654321,
  "roomId": 456789123,
  "checkIn": "2024-01-15",
  "checkOut": "2024-01-20",
  "status": "booked"
}
```

**Response:** `201 Created`
```json
{
  "id": 123456789,
  "userId": 987654321,
  "roomId": 456789123,
  "status": "booked",
  "checkIn": "2024-01-15",
  "checkOut": "2024-01-20"
}
```

**Errors:**
- `400 Bad Request` - Invalid userId, roomId, or checkOut <= checkIn
- `401 Unauthorized` - Missing or invalid admin token

---

### 3. Get Booking by ID

**Endpoint:** `GET /api/v1/bookings/{booking_id}`

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
  "id": 123456789,
  "userId": 987654321,
  "roomId": 456789123,
  "status": "booked",
  "checkIn": "2024-01-15",
  "checkOut": "2024-01-20"
}
```

**Errors:**
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Booking not found

---

### 4. Update Booking

**Endpoint:** `PUT /api/v1/bookings/{booking_id}`

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Request Body:** (all fields optional)
```json
{
  "userId": 987654321,
  "roomId": 456789123,
  "checkIn": "2024-01-16",
  "checkOut": "2024-01-21",
  "status": "confirmed"
}
```

**Response:**
```json
{
  "id": 123456789,
  "userId": 987654321,
  "roomId": 456789123,
  "status": "confirmed",
  "checkIn": "2024-01-16",
  "checkOut": "2024-01-21"
}
```

**Errors:**
- `400 Bad Request` - Invalid input or checkOut <= checkIn
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Booking not found

---

### 5. Delete Booking

**Endpoint:** `DELETE /api/v1/bookings/{booking_id}`

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response:** `204 No Content`

**Errors:**
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Booking not found

---

## Configuration

### Setting Up OAuth Clients

Configure admin OAuth clients in the `.env` file:

```bash
ADMIN_OAUTH_CLIENTS=[{"provider":"google","client_id":"your-client-id","client_secret":"your-secret"},{"provider":"azuread","client_id":"azure-client-id","client_secret":"azure-secret"}]
```

**Client Structure:**
- `provider`: OAuth provider name (e.g., "google", "azuread", "okta")
- `client_id`: OAuth client ID from provider
- `client_secret`: OAuth client secret from provider

**Example for Google:**
```json
{
  "provider": "google",
  "client_id": "123456-abcdef.apps.googleusercontent.com",
  "client_secret": "GOCSPX-abcdef123456"
}
```

### JWT Configuration

```bash
JWT_SECRET=your-256-bit-secret-key
JWT_EXPIRES_MIN=60
```

**Important:** Use a strong, random secret in production. Generate with:
```bash
openssl rand -base64 32
```

---

## Security Features

### 1. Admin Scope Enforcement

All admin endpoints use the `require_admin_scope` dependency:

```python
from src.api.security import require_admin_scope

@router.get("/admin/resource")
async def admin_route(admin: dict = Depends(require_admin_scope)):
    # Only accessible with valid admin token
    pass
```

### 2. Token Validation

Tokens are validated for:
- Valid signature (HMAC SHA256)
- Not expired (`exp` claim)
- Not used before valid time (`nbf` claim)
- Contains required `admin` scope

### 3. Authorization Code Security

- Codes expire after 5 minutes
- Single-use only (consumed after token exchange)
- Validated against original redirect_uri
- Stored in-memory (ephemeral for mock implementation)

---

## Testing

### Manual Testing with cURL

#### 1. Get Authorization Code

```bash
curl -v "http://localhost:3001/api/v1/oauth/authorize?response_type=code&client_id=mock-google-client&redirect_uri=http://localhost:3000/callback&state=test123"
```

Follow the 302 redirect to extract the `code` parameter.

#### 2. Exchange Code for Token

```bash
curl -X POST http://localhost:3001/api/v1/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "authorization_code",
    "code": "<code_from_step_1>",
    "redirect_uri": "http://localhost:3000/callback",
    "client_id": "mock-google-client",
    "client_secret": "mock-google-secret"
  }'
```

#### 3. Test Admin Me Endpoint

```bash
curl http://localhost:3001/api/v1/admin/me \
  -H "Authorization: Bearer <access_token>"
```

#### 4. List Bookings

```bash
curl http://localhost:3001/api/v1/bookings?limit=10 \
  -H "Authorization: Bearer <access_token>"
```

#### 5. Create Booking

```bash
curl -X POST http://localhost:3001/api/v1/bookings \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": 123456789,
    "roomId": 987654321,
    "checkIn": "2024-01-15",
    "checkOut": "2024-01-20",
    "status": "booked"
  }'
```

---

## Implementation Details

### Database Schema

Bookings use UUID primary keys internally but are exposed as integers via the API for compatibility with the OpenAPI specification. The conversion is handled transparently by the router layer.

**ORM Model:**
```python
class Booking(Base):
    id: UUID (PK)
    user_id: UUID (FK -> users.id)
    room_id: UUID (FK -> rooms.id)
    status: BookingStatus (enum)
    check_in: date
    check_out: date
    guests: int
    special_requests: str (optional)
```

### Scope Verification

The `require_admin_scope` helper in `security.py`:
1. Extracts and decodes the JWT from Authorization header
2. Validates token signature and expiration
3. Checks for `admin` in the `scope` claim (space-separated)
4. Raises `401 Unauthorized` if validation fails

### SQLAlchemy Integration

Admin bookings router uses SQLAlchemy ORM via the `get_db()` dependency:

```python
from sqlalchemy.orm import Session
from src.api.db import get_db

@router.get("/bookings")
async def list_bookings(db: Session = Depends(get_db)):
    bookings = db.query(BookingORM).all()
    return bookings
```

---

## Production Considerations

### ⚠️ Mock OAuth Flow Warning

The current OAuth implementation is a **MOCK** for development/testing only:

- Authorization codes stored in-memory (lost on restart)
- No persistent client registry
- Simplified validation
- No refresh tokens
- No PKCE support

**For production:**
1. Use a real OAuth2 provider (Google, Azure AD, Okta, Auth0)
2. Implement proper client registration and validation
3. Add refresh token support
4. Implement PKCE for additional security
5. Use persistent storage for authorization codes
6. Add rate limiting and abuse prevention

### Security Best Practices

1. **Always use HTTPS** in production
2. **Validate redirect_uri** against a whitelist
3. **Use strong JWT secrets** (256-bit minimum)
4. **Implement token rotation** for long-lived sessions
5. **Add audit logging** for all admin actions
6. **Enable CORS** only for trusted admin panel domains
7. **Implement rate limiting** on token endpoints

---

## Troubleshooting

### "admin_scope_required" Error

**Cause:** Token doesn't contain `admin` scope

**Solution:** Ensure the token was obtained via the OAuth flow and contains `"scope": "admin"`

### "Unknown client_id" Error

**Cause:** Client not registered in `ADMIN_OAUTH_CLIENTS`

**Solution:** Add client to `.env` file and restart server

### "Invalid userId" or "Invalid roomId"

**Cause:** User or room doesn't exist in database

**Solution:** Ensure users and rooms are created before booking

### UUID/Integer Conversion Issues

**Note:** The API exposes integer IDs for OpenAPI compatibility, but uses UUIDs internally. This conversion may be inefficient for large datasets. Consider using UUIDs end-to-end in production.

---

## API Spec Compliance

All endpoints are fully compliant with the Admin OpenAPI specification:
- `/api/v1/oauth/authorize` ✓
- `/api/v1/oauth/token` ✓
- `/api/v1/admin/me` ✓
- `/api/v1/bookings` (POST, GET) ✓
- `/api/v1/bookings/{booking_id}` (GET, PUT, DELETE) ✓

OpenAPI spec available at: `http://localhost:3001/docs`
JSON spec: `http://localhost:3001/openapi.json`

---

## Support

For issues or questions, refer to:
- Main API documentation: `README.md`
- Database layer: `DATABASE_README.md`
- Security utilities: `src/api/security.py`
- Configuration: `src/api/config.py`
