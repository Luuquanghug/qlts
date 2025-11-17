#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để thêm dữ liệu mẫu bảo trì quá hạn (overdue maintenance records)
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

def seed_overdue_maintenance(num_records: int = 10) -> int:
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
        
        overdue_descriptions = [
            'Bảo trì định kỳ đã quá hạn - cần xử lý ngay',
            'Kiểm tra và bảo dưỡng thiết bị đã quá hạn',
            'Thay thế linh kiện hỏng - đã quá hạn',
            'Nâng cấp phần mềm hệ thống - cần thực hiện gấp',
            'Vệ sinh bên trong và bên ngoài - đã quá hạn',
            'Kiểm tra hiệu suất hoạt động - đã quá thời hạn',
            'Sửa chữa lỗi phần cứng - cần xử lý ngay',
            'Cập nhật driver và firmware - đã quá hạn',
            'Kiểm tra an toàn điện - đã quá thời hạn',
            'Bảo trì phòng ngừa - cần thực hiện gấp',
            'Bảo trì khẩn cấp - đã quá hạn nhiều ngày',
            'Kiểm tra định kỳ - đã bỏ lỡ lịch bảo trì'
        ]
        
        for i in range(num_records):
            a = random.choice(assets)
            
            # Tạo ngày bảo trì trong quá khứ (từ 60-200 ngày trước)
            days_ago = random.randint(60, 200)
            mdate = today - timedelta(days=days_ago)
            
            # Tạo ngày hết hạn tiếp theo trong QUÁ KHỨ (quá hạn từ 1-90 ngày)
            overdue_days = random.randint(1, 90)
            next_due = today - timedelta(days=overdue_days)
            
            mtype, mtype_desc = random.choice(maintenance_types)
            
            rec = MaintenanceRecord(
                asset_id=a.id,
                maintenance_date=mdate,
                type=mtype,
                description=f'{mtype_desc}: {random.choice(overdue_descriptions)}',
                vendor=random.choice(vendors),
                person_in_charge=random.choice(persons),
                cost=random.randint(100_000, 10_000_000),
                next_due_date=next_due,  # Ngày hết hạn đã qua
                status='scheduled'  # Đã lên lịch nhưng chưa thực hiện
            )
            db.session.add(rec)
            created += 1
        
        db.session.commit()
        return created

if __name__ == '__main__':
    print("Đang thêm dữ liệu mẫu bảo trì QUÁ HẠN...")
    n = seed_overdue_maintenance(10)  # Thêm 10 bản ghi quá hạn
    print(f"✅ Đã tạo thành công {n} bản ghi bảo trì quá hạn!")
    print("Các bản ghi này sẽ xuất hiện trong phần 'Bản ghi quá hạn' của ứng dụng.")








































