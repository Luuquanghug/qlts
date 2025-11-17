#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để thêm dữ liệu bảo trì từ các tháng trước (dữ liệu lịch sử)
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from datetime import datetime, timedelta, date
import random

from app import app, db
from models import Asset, MaintenanceRecord

def seed_historical_maintenance():
    """Thêm dữ liệu bảo trì từ các tháng trước"""
    with app.app_context():
        assets = Asset.query.all()
        if not assets:
            print("Không tìm thấy tài sản. Vui lòng tạo tài sản trước.")
            return 0
        
        print(f"Tìm thấy {len(assets)} tài sản.")
        
        today = datetime.utcnow().date()
        current_year = today.year
        current_month = today.month
        
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
            'Công ty XYZ',
            'Công ty Bảo trì IT',
            'Dịch vụ Kỹ thuật số'
        ]
        
        persons = [
            'Nguyễn Văn A',
            'Trần Thị B',
            'Lê Văn C',
            'Phạm Thị D',
            'Hoàng Văn E',
            'Kỹ thuật viên 1',
            'Kỹ thuật viên 2',
            'Kỹ thuật viên 3'
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
            'Bảo trì phòng ngừa',
            'Thay thế pin',
            'Kiểm tra kết nối mạng',
            'Cập nhật phần mềm bảo mật',
            'Kiểm tra hệ thống làm mát',
            'Bảo trì ổ cứng'
        ]
        
        statuses = ['completed', 'scheduled', 'in_progress', 'cancelled']
        status_weights = [0.6, 0.2, 0.15, 0.05]  # Tỷ lệ trạng thái
        
        created = 0
        
        # Tạo dữ liệu cho 12 tháng trước (từ tháng hiện tại trở về)
        for month_offset in range(12):
            # Tính tháng và năm
            target_month = current_month - month_offset
            target_year = current_year
            
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            # Số bản ghi cho mỗi tháng (ngẫu nhiên từ 3-8)
            num_records = random.randint(3, 8)
            
            # Tạo các ngày trong tháng
            if target_month == 12:
                days_in_month = (date(target_year + 1, 1, 1) - timedelta(days=1)).day
            else:
                days_in_month = (date(target_year, target_month + 1, 1) - timedelta(days=1)).day
            
            for i in range(num_records):
                a = random.choice(assets)
                
                # Chọn ngày ngẫu nhiên trong tháng
                day = random.randint(1, days_in_month)
                mdate = date(target_year, target_month, day)
                
                # Tránh tạo dữ liệu trong tương lai
                if mdate > today:
                    continue
                
                # Tạo ngày hết hạn tiếp theo (30, 60, 90, 180, 365 ngày)
                next_due_days = random.choice([30, 60, 90, 180, 365])
                next_due = mdate + timedelta(days=next_due_days)
                
                # Chọn loại bảo trì
                mtype, mtype_desc = random.choice(maintenance_types)
                
                # Chọn trạng thái theo tỷ lệ
                status = random.choices(statuses, weights=status_weights)[0]
                
                # Chi phí ngẫu nhiên (có thể không có chi phí cho một số bản ghi)
                has_cost = random.random() > 0.2  # 80% có chi phí
                cost = random.randint(100_000, 5_000_000) if has_cost else None
                
                # Kiểm tra xem bản ghi đã tồn tại chưa (tránh trùng lặp)
                existing = MaintenanceRecord.query.filter_by(
                    asset_id=a.id,
                    maintenance_date=mdate,
                    type=mtype
                ).first()
                
                if existing:
                    continue
                
                rec = MaintenanceRecord(
                    asset_id=a.id,
                    maintenance_date=mdate,
                    type=mtype,
                    description=f'{mtype_desc}: {random.choice(descriptions)}',
                    vendor=random.choice(vendors) if random.random() > 0.3 else None,
                    person_in_charge=random.choice(persons),
                    cost=cost,
                    next_due_date=next_due if status in ['scheduled', 'in_progress'] else None,
                    status=status,
                    created_at=datetime.combine(mdate, datetime.min.time()),
                    updated_at=datetime.combine(mdate, datetime.min.time())
                )
                db.session.add(rec)
                created += 1
        
        # Tạo thêm một số bản ghi cho năm trước
        prev_year = current_year - 1
        for month in range(1, 13):
            num_records = random.randint(2, 5)
            
            if month == 12:
                days_in_month = (date(prev_year + 1, 1, 1) - timedelta(days=1)).day
            else:
                days_in_month = (date(prev_year, month + 1, 1) - timedelta(days=1)).day
            
            for i in range(num_records):
                a = random.choice(assets)
                day = random.randint(1, days_in_month)
                mdate = date(prev_year, month, day)
                
                next_due_days = random.choice([30, 60, 90, 180, 365])
                next_due = mdate + timedelta(days=next_due_days)
                
                mtype, mtype_desc = random.choice(maintenance_types)
                status = random.choices(statuses, weights=[0.7, 0.15, 0.1, 0.05])[0]  # Năm trước chủ yếu completed
                
                has_cost = random.random() > 0.2
                cost = random.randint(100_000, 5_000_000) if has_cost else None
                
                existing = MaintenanceRecord.query.filter_by(
                    asset_id=a.id,
                    maintenance_date=mdate,
                    type=mtype
                ).first()
                
                if existing:
                    continue
                
                rec = MaintenanceRecord(
                    asset_id=a.id,
                    maintenance_date=mdate,
                    type=mtype,
                    description=f'{mtype_desc}: {random.choice(descriptions)}',
                    vendor=random.choice(vendors) if random.random() > 0.3 else None,
                    person_in_charge=random.choice(persons),
                    cost=cost,
                    next_due_date=next_due if status in ['scheduled', 'in_progress'] else None,
                    status=status,
                    created_at=datetime.combine(mdate, datetime.min.time()),
                    updated_at=datetime.combine(mdate, datetime.min.time())
                )
                db.session.add(rec)
                created += 1
        
        try:
            db.session.commit()
            print(f"Đã commit {created} bản ghi vào database.")
        except Exception as e:
            print(f"Lỗi khi commit: {e}")
            db.session.rollback()
            return 0
        
        return created

if __name__ == '__main__':
    try:
        print("Đang thêm dữ liệu bảo trì lịch sử từ các tháng trước...")
        print("(Dữ liệu sẽ được phân bổ đều cho 12 tháng trước và năm trước)")
        n = seed_historical_maintenance()
        if n > 0:
            print(f"✅ Đã tạo thành công {n} bản ghi bảo trì lịch sử!")
            print("   Dữ liệu đã được phân bổ cho các tháng khác nhau trong năm hiện tại và năm trước.")
        else:
            print("⚠️ Không tạo được bản ghi mới. Có thể đã tồn tại hoặc có lỗi.")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

