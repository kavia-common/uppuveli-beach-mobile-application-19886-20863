# Frontend <-> Backend Entity Mapping

Use this guide to align Flutter models with BackendAPI entities/schemas.

Mobile -> BackendAPI (SQLAlchemy/Pydantic)
- User -> src/db/models.User (UserOut)
- Room -> src/db/models.Room (RoomOut)
- Booking -> src/db/models.Booking (BookingOut)
- Payment -> src/db/models.Payment (PaymentOut)
- LoyaltyAccount -> src/db/models.LoyaltyAccount (LoyaltyAccountOut)
- LoyaltyHistoryEntry -> src/db/models.LoyaltyHistory (LoyaltyHistoryOut)
- Referral -> src/db/models.Referral (ReferralOut)
- NotificationItem -> src/db/models.Notification (NotificationOut)
- ChatMessage -> src/db/models.ChatMessage (ChatMessageOut)
- BoutiqueItem -> src/db/models.BoutiqueItem (BoutiqueItemOut)

Suggested Flutter model fields (minimal to satisfy tests):
- User: id, email, name, phone, isActive
- Room: id, roomNumber, roomType, price, isAvailable, description
- Booking: id, userId, roomId, status, checkIn, checkOut
- Payment: id, bookingId, amount, currency, status, method, externalId
- LoyaltyAccount: id, userId, points, tier
- LoyaltyHistoryEntry: id, accountId, change, reason
- Referral: id, referrerId, refereeId, code, rewards
- NotificationItem: id, userId, message, isRead, type
- ChatMessage: id, userId, message, timestamp
- BoutiqueItem: id, name, description, price, stock, isActive

Notes:
- Keep naming consistent across API and Flutter where possible.
- See interfaces/openapi.json for exact API contracts.
- For mobile tests referencing package:MobileApplication/... ensure lib/ contains matching paths.
