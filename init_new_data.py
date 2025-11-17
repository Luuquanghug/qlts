#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để khởi tạo dữ liệu mẫu cho hệ thống quản lý tài sản với cấu trúc mới
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app
from models import db, Role, User, AssetType, Asset
from datetime import datetime, date

def init_new_sample_data():
    """Khởi tạo dữ liệu mẫu với cấu trúc mới"""
    
    with app.app_context():
        # Tạo bảng
        db.create_all()
        
        # Xóa tất cả dữ liệu cũ
        db.drop_all()
        db.create_all()
        
        # Kiểm tra xem đã có dữ liệu chưa
        if Role.query.first() is not None:
            print("Dữ liệu đã tồn tại. Bỏ qua khởi tạo.")
            return
        
        print("Đang khởi tạo dữ liệu mẫu với cấu trúc mới...")
        
        # Tạo roles
        roles = [
            Role(name="admin", description="Quản trị viên hệ thống"),
            Role(name="manager", description="Quản lý tài sản"),
            Role(name="user", description="Người dùng thông thường"),
        ]
        
        for role in roles:
            db.session.add(role)
        
        db.session.commit()
        
        # Tạo users
        admin_role = Role.query.filter_by(name="admin").first()
        manager_role = Role.query.filter_by(name="manager").first()
        user_role = Role.query.filter_by(name="user").first()
        
        users = [
            User(
                username="admin",
                email="admin@company.com",
                role_id=admin_role.id,
                is_active=True
            ),
            User(
                username="manager1",
                email="manager@company.com",
                role_id=manager_role.id,
                is_active=True
            ),
            User(
                username="user1",
                email="user1@company.com",
                role_id=user_role.id,
                is_active=True
            ),
            User(
                username="user2",
                email="user2@company.com",
                role_id=user_role.id,
                is_active=True
            ),
        ]
        
        for user in users:
            user.set_password("password123")  # Mật khẩu mặc định
            db.session.add(user)
        
        db.session.commit()
        
        # Tạo asset types
        asset_types = [
            AssetType(name="Máy tính", description="Máy tính để bàn, laptop, máy tính bảng"),
            AssetType(name="Thiết bị văn phòng", description="Máy in, máy photocopy, máy fax"),
            AssetType(name="Nội thất", description="Bàn ghế, tủ, kệ"),
            AssetType(name="Thiết bị mạng", description="Router, switch, modem"),
            AssetType(name="Thiết bị điện tử", description="Điện thoại, máy ảnh, loa"),
        ]
        
        for asset_type in asset_types:
            db.session.add(asset_type)
        
        db.session.commit()
        
        # Tạo assets
        admin_user = User.query.filter_by(username="admin").first()
        manager_user = User.query.filter_by(username="manager1").first()
        user1 = User.query.filter_by(username="user1").first()
        user2 = User.query.filter_by(username="user2").first()
        
        computer_type = AssetType.query.filter_by(name="Máy tính").first()
        office_type = AssetType.query.filter_by(name="Thiết bị văn phòng").first()
        furniture_type = AssetType.query.filter_by(name="Nội thất").first()
        network_type = AssetType.query.filter_by(name="Thiết bị mạng").first()
        electronic_type = AssetType.query.filter_by(name="Thiết bị điện tử").first()
        
        assets = [
            Asset(
                name="Laptop Dell XPS 13",
                price=25000000,
                quantity=1,
                status="active",
                asset_type_id=computer_type.id,
                user_id=admin_user.id,
                user_text="Laptop cao cấp cho developer",
                notes="Được cấp cho phòng IT",
                created_at=datetime.utcnow()
            ),
            Asset(
                name="Máy in HP LaserJet",
                price=3500000,
                quantity=2,
                status="active",
                asset_type_id=office_type.id,
                user_id=manager_user.id,
                user_text="Máy in laser đen trắng",
                notes="Đặt tại phòng hành chính",
                created_at=datetime.utcnow()
            ),
            Asset(
                name="Bàn làm việc gỗ",
                price=2000000,
                quantity=10,
                status="active",
                asset_type_id=furniture_type.id,
                user_id=user1.id,
                user_text="Bàn làm việc gỗ cao cấp",
                notes="Bàn tiêu chuẩn cho nhân viên",
                created_at=datetime.utcnow()
            ),
            Asset(
                name="Router Cisco",
                price=5000000,
                quantity=1,
                status="active",
                asset_type_id=network_type.id,
                user_id=admin_user.id,
                user_text="Router mạng doanh nghiệp",
                notes="Router chính của công ty",
                created_at=datetime.utcnow()
            ),
            Asset(
                name="iPhone 14 Pro",
                price=30000000,
                quantity=1,
                status="active",
                asset_type_id=electronic_type.id,
                user_id=manager_user.id,
                user_text="Điện thoại di động cao cấp",
                notes="Điện thoại công ty cho quản lý",
                created_at=datetime.utcnow()
            ),
            Asset(
                name="Máy tính để bàn HP",
                price=15000000,
                quantity=5,
                status="maintenance",
                asset_type_id=computer_type.id,
                user_id=user2.id,
                user_text="Máy tính văn phòng",
                notes="Đang bảo trì định kỳ",
                created_at=datetime.utcnow()
            ),
            Asset(
                name="Ghế văn phòng",
                price=3000000,
                quantity=15,
                status="active",
                asset_type_id=furniture_type.id,
                user_id=user1.id,
                user_text="Ghế văn phòng ergonomic",
                notes="Ghế tiêu chuẩn cho nhân viên",
                created_at=datetime.utcnow()
            ),
        ]
        
        for asset in assets:
            db.session.add(asset)
        
        db.session.commit()
        
        print("✅ Khởi tạo dữ liệu mẫu thành công!")
        print(f"   - {len(roles)} roles")
        print(f"   - {len(users)} users")
        print(f"   - {len(asset_types)} asset types")
        print(f"   - {len(assets)} assets")
        print("\n🔐 Thông tin đăng nhập:")
        print("   - Admin: admin / password123")
        print("   - Manager: manager1 / password123")
        print("   - User: user1 / password123")

if __name__ == "__main__":
    init_new_sample_data()
