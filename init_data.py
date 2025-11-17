#!/usr/bin/env python3
"""
Script để khởi tạo dữ liệu mẫu cho hệ thống quản lý tài sản
"""

from app import app
from models import db, Category, Employee, Asset
from datetime import datetime, date

def init_sample_data():
    """Khởi tạo dữ liệu mẫu"""
    
    with app.app_context():
        # Tạo bảng
        db.create_all()
        
        # Kiểm tra xem đã có dữ liệu chưa
        if Category.query.first() is not None:
            print("Dữ liệu đã tồn tại. Bỏ qua khởi tạo.")
            return
        
        print("Đang khởi tạo dữ liệu mẫu...")
        
        # Tạo danh mục
        categories = [
            Category(name="Máy tính", description="Máy tính để bàn, laptop, máy tính bảng"),
            Category(name="Thiết bị văn phòng", description="Máy in, máy photocopy, máy fax"),
            Category(name="Nội thất", description="Bàn ghế, tủ, kệ"),
            Category(name="Thiết bị mạng", description="Router, switch, modem"),
            Category(name="Thiết bị điện tử", description="Điện thoại, máy ảnh, loa"),
        ]
        
        for category in categories:
            db.session.add(category)
        
        # Tạo nhân viên
        employees = [
            Employee(name="Nguyễn Văn An", email="an.nguyen@company.com", department="IT", position="Developer"),
            Employee(name="Trần Thị Bình", email="binh.tran@company.com", department="HR", position="Manager"),
            Employee(name="Lê Văn Cường", email="cuong.le@company.com", department="Finance", position="Accountant"),
            Employee(name="Phạm Thị Dung", email="dung.pham@company.com", department="Marketing", position="Designer"),
            Employee(name="Hoàng Văn Em", email="em.hoang@company.com", department="IT", position="System Admin"),
        ]
        
        for employee in employees:
            db.session.add(employee)
        
        db.session.commit()
        
        # Tạo tài sản
        assets = [
            Asset(
                name="Laptop Dell XPS 13",
                description="Laptop cao cấp cho developer",
                category_id=1,
                employee_id=1,
                purchase_date=date(2023, 1, 15),
                purchase_price=25000000,
                status="active"
            ),
            Asset(
                name="Máy in HP LaserJet",
                description="Máy in laser đen trắng",
                category_id=2,
                employee_id=2,
                purchase_date=date(2023, 2, 20),
                purchase_price=3500000,
                status="active"
            ),
            Asset(
                name="Bàn làm việc gỗ",
                description="Bàn làm việc gỗ cao cấp",
                category_id=3,
                employee_id=3,
                purchase_date=date(2023, 3, 10),
                purchase_price=2000000,
                status="active"
            ),
            Asset(
                name="Router Cisco",
                description="Router mạng doanh nghiệp",
                category_id=4,
                employee_id=5,
                purchase_date=date(2023, 4, 5),
                purchase_price=5000000,
                status="active"
            ),
            Asset(
                name="iPhone 14 Pro",
                description="Điện thoại di động cao cấp",
                category_id=5,
                employee_id=4,
                purchase_date=date(2023, 5, 12),
                purchase_price=30000000,
                status="active"
            ),
            Asset(
                name="Máy tính để bàn HP",
                description="Máy tính văn phòng",
                category_id=1,
                employee_id=2,
                purchase_date=date(2022, 12, 1),
                purchase_price=15000000,
                status="maintenance"
            ),
            Asset(
                name="Ghế văn phòng",
                description="Ghế văn phòng ergonomic",
                category_id=3,
                employee_id=1,
                purchase_date=date(2023, 1, 20),
                purchase_price=3000000,
                status="active"
            ),
        ]
        
        for asset in assets:
            db.session.add(asset)
        
        db.session.commit()
        
        print("✅ Khởi tạo dữ liệu mẫu thành công!")
        print(f"   - {len(categories)} danh mục")
        print(f"   - {len(employees)} nhân viên")
        print(f"   - {len(assets)} tài sản")

if __name__ == "__main__":
    init_sample_data()
