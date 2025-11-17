#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để thêm dữ liệu mẫu bảo trì thiết bị IT
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from datetime import datetime, timedelta
import random

from app import app, db
from models import Asset, MaintenanceRecord

def seed_maintenance(num_records: int = 10) -> int:
    with app.app_context():
        assets = Asset.query.all()
        if not assets:
            print("Không tìm thấy tài sản. Vui lòng tạo tài sản trước.")
            return 0
        
        today = datetime.utcnow().date()
        created = 0
        
        # Loại bảo trì với mô tả tiếng Việt
        maintenance_types = [
            ('maintenance', 'Bảo trì định kỳ'),
            ('repair', 'Sửa chữa'),
            ('inspection', 'Kiểm tra'),
            ('upgrade', 'Nâng cấp'),
            ('cleaning', 'Vệ sinh')
        ]
        
        vendors = [
            'FPT Services',
            'Viettel',
            'NCC A',
            'NCC B',
            'Công ty TNHH ABC',
            'Công ty XYZ'
        ]
        
        persons = [
            'Nguyễn Văn A',
            'Trần Thị B',
            'Lê Văn C',
            'Phạm Thị D',
            'Admin',
            'Kỹ thuật viên 1',
            'Kỹ thuật viên 2'
        ]
        
        descriptions = [
            'Bảo trì định kỳ theo lịch',
            'Kiểm tra và bảo dưỡng thiết bị',
            'Thay thế linh kiện hỏng',
            'Nâng cấp phần mềm hệ thống',
            'Vệ sinh bên trong và bên ngoài',
            'Kiểm tra hiệu suất hoạt động',
            'Sửa chữa lỗi phần cứng',
            'Cập nhật driver và firmware',
            'Kiểm tra an toàn điện',
            'Bảo trì phòng ngừa'
        ]
        
        for i in range(num_records):
            a = random.choice(assets)
            days_ago = random.randint(0, 180)
            mdate = today - timedelta(days=days_ago)
            
            # Tạo ngày hết hạn tiếp theo (30, 60, 90, 180, 365 ngày)
            next_due_days = random.choice([30, 60, 90, 180, 365])
            next_due = mdate + timedelta(days=next_due_days)
            
            mtype, mtype_desc = random.choice(maintenance_types)
            
            rec = MaintenanceRecord(
                asset_id=a.id,
                maintenance_date=mdate,
                type=mtype,
                description=f'{mtype_desc}: {random.choice(descriptions)}',
                vendor=random.choice(vendors),
                person_in_charge=random.choice(persons),
                cost=random.randint(100_000, 10_000_000),
                next_due_date=next_due,
                status=random.choice(['completed', 'scheduled'])
            )
            db.session.add(rec)
            created += 1
        
        db.session.commit()
        return created

if __name__ == '__main__':
    print("Đang thêm dữ liệu mẫu bảo trì...")
    n = seed_maintenance(15)  # Thêm 15 bản ghi
    print(f"✅ Đã tạo thành công {n} bản ghi bảo trì!")


