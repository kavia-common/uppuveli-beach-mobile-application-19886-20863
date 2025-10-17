# Frontend Quick Reference (Models and Minimal Fields)

Use these minimal fields to create Dart model stubs that match tests and map to BackendAPI entities.

- User (src/db/models.py: User)
  - id: int
  - email: String
  - name: String?
  - phone: String?
  - isActive: bool

- Room (Room)
  - id: int
  - roomNumber: String
  - roomType: String
  - price: double
  - isAvailable: bool
  - description: String?

- Booking (Booking)
  - id: int
  - userId: int
  - roomId: int
  - status: String
  - checkIn: DateTime / Date
  - checkOut: DateTime / Date

- Payment (Payment)
  - id: int
  - bookingId: int
  - amount: double
  - currency: String
  - status: String
  - method: String
  - externalId: String?

- Loyalty (LoyaltyAccount + LoyaltyHistory)
  - Loyalty:
    - userId: int
    - points: int
    - history: List<LoyaltyHistoryEntry>
  - LoyaltyHistoryEntry:
    - date: DateTime
    - change: int
    - reason: String

- Referral (Referral)
  - id: int
  - code: String
  - rewards: int
  - userId (referrerId): int?

- NotificationItem (Notification)
  - id: int
  - userId: int
  - message: String
  - read: bool

- ChatMessage (ChatMessage)
  - id: int
  - userId: int
  - message: String
  - timestamp: DateTime

State
- AuthState:
  - isAuthenticated: bool
  - token: String?
  - email: String?
  - Methods: login(), logout(), register()

Screens (minimal placeholders)
- LoginScreen: email/password TextFields, login Button
- RegisterScreen: name/email/password, register Button
- HomeScreen: shows title, conditional greeting if AuthState.isAuthenticated
- RoomsListScreen: takes list of Room, renders basic ListView

Notes
- Package imports in tests use: package:MobileApplication/...
  Ensure your Flutter project's name in pubspec.yaml is "MobileApplication" to satisfy these imports.
- Provide const constructors and fromJson/toJson where useful.
- Keep fields required by tests as non-nullable; use default values for const instances in tests.
