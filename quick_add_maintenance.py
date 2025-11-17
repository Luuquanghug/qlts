# -*- coding: utf-8 -*-
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app, db
from models import Asset, MaintenanceRecord
from datetime import datetime, timedelta, date
import random

with app.app_context():
    try:
        assets = Asset.query.all()
        print(f"Tim thay {len(assets)} tai san")
        
        if not assets:
            print("Khong co tai san!")
            sys.exit(1)
        
        today = datetime.utcnow().date()
        created = 0
        print(f"Bat dau tao du lieu tu ngay {today}...")
        
        # Tạo dữ liệu cho 12 tháng trước
        for month_offset in range(12):
            target_month = today.month - month_offset
            target_year = today.year
            
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            # Số bản ghi mỗi tháng
            num_records = random.randint(3, 8)
            
            # Tính số ngày trong tháng
            if target_month == 12:
                days_in_month = (date(target_year + 1, 1, 1) - timedelta(days=1)).day
            else:
                days_in_month = (date(target_year, target_month + 1, 1) - timedelta(days=1)).day
            
            for i in range(num_records):
                asset = random.choice(assets)
                day = random.randint(1, days_in_month)
                mdate = date(target_year, target_month, day)
                
                if mdate > today:
                    continue
                
                status = random.choice(['completed', 'scheduled', 'in_progress'])
                has_cost = random.random() > 0.2
                cost = random.randint(100000, 5000000) if has_cost else None
                
                rec = MaintenanceRecord(
                    asset_id=asset.id,
                    maintenance_date=mdate,
                    type=random.choice(['maintenance', 'repair', 'inspection']),
                    description=f'Bao tri dinh ky thang {target_month}/{target_year}',
                    vendor=random.choice(['FPT', 'Viettel', 'NCC A']) if random.random() > 0.3 else None,
                    person_in_charge=random.choice(['Nguyen Van A', 'Tran Thi B', 'Le Van C']),
                    cost=cost,
                    next_due_date=mdate + timedelta(days=random.choice([30, 60, 90, 180, 365])) if status in ['scheduled', 'in_progress'] else None,
                    status=status
                )
                db.session.add(rec)
                created += 1
        
        # Tạo dữ liệu cho năm trước
        prev_year = today.year - 1
        for month in range(1, 13):
            num_records = random.randint(2, 5)
            
            if month == 12:
                days_in_month = (date(prev_year + 1, 1, 1) - timedelta(days=1)).day
            else:
                days_in_month = (date(prev_year, month + 1, 1) - timedelta(days=1)).day
            
            for i in range(num_records):
                asset = random.choice(assets)
                day = random.randint(1, days_in_month)
                mdate = date(prev_year, month, day)
                
                status = random.choice(['completed', 'scheduled'])
                has_cost = random.random() > 0.2
                cost = random.randint(100000, 5000000) if has_cost else None
                
                rec = MaintenanceRecord(
                    asset_id=asset.id,
                    maintenance_date=mdate,
                    type=random.choice(['maintenance', 'repair', 'inspection']),
                    description=f'Bao tri dinh ky thang {month}/{prev_year}',
                    vendor=random.choice(['FPT', 'Viettel', 'NCC A']) if random.random() > 0.3 else None,
                    person_in_charge=random.choice(['Nguyen Van A', 'Tran Thi B', 'Le Van C']),
                    cost=cost,
                    next_due_date=mdate + timedelta(days=random.choice([30, 60, 90, 180, 365])) if status == 'scheduled' else None,
                    status=status
                )
                db.session.add(rec)
                created += 1
        
        try:
            db.session.commit()
            print(f"Da tao thanh cong {created} ban ghi bao tri!")
        except Exception as e:
            print(f"Loi khi commit: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
    except Exception as e:
        print(f"Loi: {e}")
        import traceback
        traceback.print_exc()
