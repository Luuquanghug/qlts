#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bulk-create users for the asset management app.
Run: py add_users.py
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app
from models import db, User, Role


def ensure_role(role_name: str) -> int:
    role = Role.query.filter_by(name=role_name).first()
    if role is None:
        role = Role(name=role_name, description=f"Auto created role: {role_name}")
        db.session.add(role)
        db.session.commit()
    return role.id


def create_users(users_to_create: list[dict]):
    created = 0
    skipped = 0
    for u in users_to_create:
        if User.query.filter_by(username=u["username"]).first() is not None:
            skipped += 1
            continue
        role_id = ensure_role(u.get("role", "user"))
        user = User(
            username=u["username"],
            email=u["email"],
            role_id=role_id,
            is_active=True,
        )
        user.set_password(u.get("password", "password123"))
        db.session.add(user)
        created += 1
    db.session.commit()
    return created, skipped


# Danh sách 10 users mới
NEW_USERS = [
    {"username": "nguyenvana", "email": "nguyenvana@company.com", "role": "user", "password": "password123"},
    {"username": "tranthib", "email": "tranthib@company.com", "role": "user", "password": "password123"},
    {"username": "levanc", "email": "levanc@company.com", "role": "user", "password": "password123"},
    {"username": "phamthid", "email": "phamthid@company.com", "role": "user", "password": "password123"},
    {"username": "hoangvane", "email": "hoangvane@company.com", "role": "user", "password": "password123"},
    {"username": "manager2", "email": "manager2@company.com", "role": "manager", "password": "password123"},
    {"username": "manager3", "email": "manager3@company.com", "role": "manager", "password": "password123"},
    {"username": "user3", "email": "user3@company.com", "role": "user", "password": "password123"},
    {"username": "user4", "email": "user4@company.com", "role": "user", "password": "password123"},
    {"username": "user5", "email": "user5@company.com", "role": "user", "password": "password123"},
]


if __name__ == "__main__":
    with app.app_context():
        print("Đang thêm 10 users mới...")
        created, skipped = create_users(NEW_USERS)
        print(f"✅ Đã tạo thành công {created} users.")
        if skipped > 0:
            print(f"⚠️  Đã bỏ qua {skipped} users đã tồn tại.")
        
        print("\n📋 Danh sách users vừa tạo:")
        for u in NEW_USERS:
            user = User.query.filter_by(username=u["username"]).first()
            if user:
                role = Role.query.get(user.role_id)
                print(f"   - {user.username} ({user.email}) - Role: {role.name if role else 'N/A'}")






