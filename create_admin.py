#!/usr/bin/env python3
"""
Script to create an admin user for the Quiz Application.
Run this script after setting up the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database.connection import get_db
from models.user import User
from auth.jwt import get_password_hash

def create_admin_user():
    """Create an admin user if it doesn't exist."""
    db = next(get_db())
    
    # Check if admin already exists
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        print("Admin user already exists!")
        return
    
    # Create admin user
    admin_user = User(
        name="Administrator",
        username="admin",
        password_hash=get_password_hash("admin123"),
        roles=["Admin"]
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    print("Admin user created successfully!")
    print("Username: admin")
    print("Password: admin123")
    print("Please change the password after first login!")

if __name__ == "__main__":
    create_admin_user() 