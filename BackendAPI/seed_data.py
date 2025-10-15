"""Seed sample data for testing.

This script creates sample users, rooms, and optionally a sample booking.

Usage:
    python seed_data.py
"""

import sys
import logging
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    from src.api.db import init_db_engine, get_db
    from src.api.models import User, Room, Booking, BookingStatus
    from src.api.security import hash_password
    
    logger.info("Initializing database connection...")
    init_db_engine()
    db = next(get_db())
    
    try:
        # Check existing data
        user_count = db.query(User).count()
        room_count = db.query(Room).count()
        
        logger.info(f"Current data: {user_count} users, {room_count} rooms")
        
        # Create sample user if none exist
        if user_count == 0:
            logger.info("Creating sample user...")
            user = User(
                email='guest@example.com',
                password_hash=hash_password('password123'),
                name='Test Guest',
                phone='+1234567890',
                is_active=True
            )
            db.add(user)
            db.flush()
            logger.info(f"✓ Created user: {user.email} (id: {user.id})")
        else:
            user = db.query(User).first()
            logger.info(f"Using existing user: {user.email}")
        
        # Create sample rooms if none exist
        if room_count == 0:
            logger.info("Creating sample rooms...")
            rooms_data = [
                {
                    'room_number': '101',
                    'type': 'Deluxe',
                    'price': 150.00,
                    'availability': True,
                    'max_occupancy': 2,
                    'description': 'Deluxe room with ocean view'
                },
                {
                    'room_number': '201',
                    'type': 'Suite',
                    'price': 250.00,
                    'availability': True,
                    'max_occupancy': 4,
                    'description': 'Luxury suite with private balcony'
                },
                {
                    'room_number': '102',
                    'type': 'Standard',
                    'price': 100.00,
                    'availability': True,
                    'max_occupancy': 2,
                    'description': 'Standard room with garden view'
                },
            ]
            
            for room_data in rooms_data:
                room = Room(**room_data)
                db.add(room)
                db.flush()
                logger.info(f"✓ Created room: {room.type} #{room.room_number} (id: {room.id})")
        else:
            logger.info(f"Rooms already exist: {room_count} rooms")
        
        # Optionally create a sample booking
        booking_count = db.query(Booking).count()
        if booking_count == 0:
            room = db.query(Room).filter(Room.availability == True).first()
            if room and user:
                logger.info("Creating sample booking...")
                booking = Booking(
                    user_id=user.id,
                    room_id=room.id,
                    status=BookingStatus.BOOKED,
                    check_in=date.today() + timedelta(days=7),
                    check_out=date.today() + timedelta(days=10),
                    guests=2,
                    special_requests='Early check-in if possible'
                )
                db.add(booking)
                db.flush()
                logger.info(f"✓ Created booking: {booking.id}")
        
        db.commit()
        logger.info("\n✓ Sample data seeded successfully")
        
        # Summary
        logger.info("\nDatabase Summary:")
        logger.info(f"  Users: {db.query(User).count()}")
        logger.info(f"  Rooms: {db.query(Room).count()}")
        logger.info(f"  Bookings: {db.query(Booking).count()}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
