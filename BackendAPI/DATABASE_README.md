# BackendAPI Database Layer

This document describes the SQLAlchemy-based database layer for the BackendAPI container.

## Overview

The database layer uses **SQLAlchemy ORM** with **PostgreSQL** (via psycopg2) to provide:
- Type-safe ORM models reflecting the database schema
- Relationship mappings between entities
- FastAPI dependency injection for database sessions
- Backward compatibility with asyncpg-style query helpers

## Architecture

### Components

1. **`src/api/db.py`**: Database engine, session management, and query helpers
2. **`src/api/models.py`**: SQLAlchemy ORM models and Pydantic schemas
3. **`init_db.py`**: Database initialization script

### Key Features

- **SQLAlchemy ORM Models**: All database tables are mapped to Python classes
- **Relationships**: Foreign key relationships are defined with `relationship()` 
- **Indexes**: Critical indexes defined for query performance
- **Enums**: PostgreSQL enum types mapped to Python enums
- **Backward Compatibility**: Asyncpg-style helpers (`fetch_one`, `fetch_all`, `execute`) preserved

## Database Schema

### Tables

| Table | Description |
|-------|-------------|
| `users` | Guest users (mobile app) |
| `admin_users` | Staff users (admin panel) |
| `rooms` | Hotel rooms inventory |
| `bookings` | Room reservations |
| `payments` | Payment transactions |
| `loyalty_accounts` | User loyalty point accounts |
| `loyalty_history` | Loyalty point change history |
| `referrals` | Referral codes and rewards |
| `notifications` | User notifications |
| `chat_messages` | Chat messages between users and staff |
| `boutique_items` | Boutique shop inventory |

### Key Relationships

```
User (1) ----< (N) Booking
User (1) ----< (N) Payment
User (1) ---- (1) LoyaltyAccount
User (1) ----< (N) Referral
User (1) ----< (N) Notification
User (1) ----< (N) ChatMessage

Room (1) ----< (N) Booking
Booking (1) ----< (N) Payment

LoyaltyAccount (1) ----< (N) LoyaltyHistory
```

## Usage

### Configuration

Set the `DATABASE_URL` environment variable in `.env`:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/uppuveli_beach
```

### Initialization

#### Option 1: Using init_db.py script

```bash
cd BackendAPI
python init_db.py
```

#### Option 2: Using CREATE_TABLES environment flag

Set in `.env`:
```bash
CREATE_TABLES=true
```

Then start the application:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 3001
```

### Using ORM Models in Routes

#### Example 1: Using get_db() dependency

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.db import get_db
from src.api.models import User, Booking

router = APIRouter()

@router.get("/users/{user_id}/bookings")
def get_user_bookings(user_id: str, db: Session = Depends(get_db)):
    """Get all bookings for a user using ORM."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Access related bookings via relationship
    return [
        {
            "id": str(booking.id),
            "room_id": str(booking.room_id),
            "check_in": booking.check_in,
            "check_out": booking.check_out,
            "status": booking.status.value
        }
        for booking in user.bookings
    ]
```

#### Example 2: Using backward-compatible helpers

```python
from src.api.db import fetch_one, execute

async def get_user_by_email(email: str):
    """Get user using asyncpg-style helper."""
    row = await fetch_one(
        "SELECT id, email, name FROM users WHERE email=$1",
        email
    )
    return row

async def create_booking(user_id: str, room_id: str, check_in, check_out):
    """Create booking using asyncpg-style helper."""
    await execute(
        "INSERT INTO bookings (user_id, room_id, check_in, check_out, status) "
        "VALUES ($1, $2, $3, $4, 'booked')",
        user_id, room_id, check_in, check_out
    )
```

### ORM Query Examples

#### Creating Records

```python
from src.api.models import User, Booking
from src.api.db import get_db

def create_user(db: Session):
    user = User(
        email="guest@example.com",
        name="John Doe",
        password_hash="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

#### Querying with Filters

```python
# Get active bookings
active_bookings = db.query(Booking).filter(
    Booking.status == BookingStatus.BOOKED
).all()

# Get user with eager loading of relationships
user = db.query(User).options(
    joinedload(User.bookings),
    joinedload(User.loyalty_account)
).filter(User.id == user_id).first()
```

#### Updating Records

```python
booking = db.query(Booking).filter(Booking.id == booking_id).first()
if booking:
    booking.status = BookingStatus.CONFIRMED
    db.commit()
```

#### Deleting Records

```python
db.query(Booking).filter(Booking.id == booking_id).delete()
db.commit()
```

## Model Details

### User Model

```python
class User(Base):
    __tablename__ = "users"
    
    id: UUID (PK)
    email: str (unique, indexed)
    password_hash: str
    name: str
    phone: str (optional)
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    bookings: List[Booking]
    payments: List[Payment]
    loyalty_account: LoyaltyAccount
    referrals: List[Referral]
    notifications: List[Notification]
    chat_messages: List[ChatMessage]
```

### Booking Model

```python
class Booking(Base):
    __tablename__ = "bookings"
    
    id: UUID (PK)
    user_id: UUID (FK -> users.id)
    room_id: UUID (FK -> rooms.id)
    status: BookingStatus (enum)
    check_in: date
    check_out: date
    guests: int
    special_requests: str (optional)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    user: User
    room: Room
    payments: List[Payment]
```

## Enums

### BookingStatus
- `BOOKED`
- `CONFIRMED`
- `CHECKED_IN`
- `CHECKED_OUT`
- `CANCELLED`

### PaymentStatus
- `PENDING`
- `AUTHORIZED`
- `CAPTURED`
- `REFUNDED`
- `FAILED`
- `VOIDED`

### PaymentMethod
- `STRIPE`
- `PAYPAL`
- `WALLET`
- `CASH`
- `CARD`

### NotificationType
- `SYSTEM`
- `PROMOTION`
- `BOOKING`
- `LOYALTY`
- `PAYMENT`
- `CHAT`

### NotificationStatus
- `QUEUED`
- `SENT`
- `DELIVERED`
- `READ`
- `FAILED`

## Backward Compatibility

The database layer maintains compatibility with existing router code using asyncpg-style queries:

- `await fetch_one(sql, *params)` → Returns dict or None
- `await fetch_all(sql, *params)` → Returns list of dicts
- `await execute(sql, *params)` → Returns status string
- `await execute_many(sql, param_sets)` → Returns list of status strings

**Note**: Placeholders use PostgreSQL format (`$1`, `$2`, etc.) and are automatically converted to SQLAlchemy named parameters.

## Migration Notes

### From asyncpg to SQLAlchemy

1. **Query placeholders**: `$1, $2` are automatically converted to `:param_0, :param_1`
2. **Result types**: ORM queries return model instances; raw SQL helpers return dicts
3. **Transactions**: Use `db.commit()` and `db.rollback()` with ORM sessions
4. **Connection management**: Sessions are auto-managed via `get_db()` dependency

### Existing Code Compatibility

All existing routers continue to work without modification:
- `/routers/auth.py`
- `/routers/bookings.py`
- `/routers/payments.py`
- `/routers/loyalty.py`
- `/routers/referrals.py`
- `/routers/notifications.py`
- `/routers/chat.py`
- `/routers/admin_bookings.py`

## Performance Considerations

1. **Connection Pooling**: Configured with `pool_size=5` and `max_overflow=10`
2. **Indexes**: All foreign keys and frequently queried columns are indexed
3. **Lazy Loading**: Relationships use `lazy='select'` by default
4. **Eager Loading**: Use `joinedload()` or `selectinload()` for optimizing N+1 queries

## Testing

```python
# Test database connection
python -c "from src.api.db import init_db_engine; init_db_engine(); print('✓ Connection OK')"

# Test ORM models
python -c "from src.api.models import User, Booking; print('✓ Models OK')"

# Test backward compatibility
python -c "from src.api.db import fetch_one, execute; print('✓ Helpers OK')"
```

## Troubleshooting

### Database URL not set
```
WARNING:root:DATABASE_URL is not set; database engine will not be initialized.
```
**Solution**: Set `DATABASE_URL` in `.env` file

### Cannot import name 'fetch_one'
**Solution**: Ensure you're using the updated `db.py` with backward compatibility layer

### Enum type not found
**Solution**: Run the database schema.sql to create enum types first

### Table metadata conflict
**Solution**: Use `meta_data` attribute for models (maps to `metadata` column)

## Future Enhancements

- [ ] Add Alembic for database migrations
- [ ] Implement soft deletes
- [ ] Add audit logging
- [ ] Consider async SQLAlchemy (sqlalchemy[asyncio])
- [ ] Add database health checks endpoint
