#!/usr/bin/env python3
"""
Script để chạy ứng dụng Flask
"""

from app import app, db
from sqlalchemy import inspect, text
try:
    from app import ensure_asset_columns
except ImportError:
    ensure_asset_columns = None
from models import Asset, Role, User, AssetType

if __name__ == '__main__':
    with app.app_context():
        # Tạo bảng database nếu chưa tồn tại
        db.create_all()
        # Ensure legacy tables have new nullable columns to avoid crashes without migrations
        try:
            inspector = inspect(db.engine)
            existing_user_columns = {col['name'] for col in inspector.get_columns('user')}
            ddl_statements = []
            # Add nullable columns safely if they don't exist yet
            if 'deleted_at' not in existing_user_columns:
                ddl_statements.append('ALTER TABLE "user" ADD COLUMN deleted_at TIMESTAMP NULL')
            if 'last_login' not in existing_user_columns:
                ddl_statements.append('ALTER TABLE "user" ADD COLUMN last_login TIMESTAMP NULL')
            for ddl in ddl_statements:
                try:
                    db.session.execute(text(ddl))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            # Non-fatal: continue startup; queries will raise if schema is still incompatible
            pass
        # Ensure asset table has all required columns
        try:
            inspector = inspect(db.engine)
            existing_asset_columns = {col['name'] for col in inspector.get_columns('asset')}
            asset_ddl_statements = []
            # Add nullable columns safely if they don't exist yet
            if 'purchase_date' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN purchase_date DATE NULL')
            if 'device_code' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN device_code VARCHAR(100) NULL')
            if 'condition_label' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN condition_label VARCHAR(100) NULL')
            if 'user_text' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN user_text TEXT NULL')
            if 'deleted_at' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN deleted_at TIMESTAMP NULL')
            for ddl in asset_ddl_statements:
                try:
                    db.session.execute(text(ddl))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            # Non-fatal: continue startup
            pass
        # Ensure asset_type table has all required columns
        try:
            inspector = inspect(db.engine)
            existing_asset_type_columns = {col['name'] for col in inspector.get_columns('asset_type')}
            asset_type_ddl_statements = []
            # Add nullable columns safely if they don't exist yet
            if 'deleted_at' not in existing_asset_type_columns:
                asset_type_ddl_statements.append('ALTER TABLE "asset_type" ADD COLUMN deleted_at TIMESTAMP NULL')
            for ddl in asset_type_ddl_statements:
                try:
                    db.session.execute(text(ddl))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            # Non-fatal: continue startup
            pass
        # Ensure maintenance_record table has all required columns
        try:
            inspector = inspect(db.engine)
            existing_maintenance_columns = {col['name'] for col in inspector.get_columns('maintenance_record')}
            maintenance_ddl_statements = []
            # Add nullable columns safely if they don't exist yet
            if 'deleted_at' not in existing_maintenance_columns:
                maintenance_ddl_statements.append('ALTER TABLE "maintenance_record" ADD COLUMN deleted_at TIMESTAMP NULL')
            for ddl in maintenance_ddl_statements:
                try:
                    db.session.execute(text(ddl))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            # Non-fatal: continue startup
            pass
        # Auto-bootstrap minimal data so login always works on first run
        try:
            if Role.query.count() == 0:
                roles = [
                    Role(name='admin', description='Quản trị'),
                    Role(name='manager', description='Quản lý'),
                    Role(name='user', description='Nhân viên'),
                ]
                db.session.add_all(roles)
                db.session.commit()
            # Ensure an admin exists
            admin_username = app.config.get('ADMIN_USERNAME', 'admin')
            admin_email = app.config.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
            if User.query.filter_by(username=admin_username).first() is None:
                admin_role = Role.query.filter_by(name='admin').first()
                if not admin_role:
                    admin_role = Role(name='admin', description='Quản trị')
                    db.session.add(admin_role)
                    db.session.commit()
                u = User(username=admin_username, email=admin_email, role_id=admin_role.id, is_active=True)
                u.set_password(admin_password)
                db.session.add(u)
                db.session.commit()
        except Exception as e:
            # Non-fatal, print diagnostic
            print("Bootstrap error:", e)
        # Ensure new optional columns exist
        if ensure_asset_columns:
            try:
                ensure_asset_columns()
            except Exception:
                pass
    import os
    # Avoid emojis to prevent UnicodeEncodeError on some Windows consoles
    host = os.getenv('HOST', '0.0.0.0')
    try:
        port = int(os.getenv('PORT', '5000'))
    except Exception:
        port = 5000
    print("Khoi dong ung dung Quan ly Tai san...")
    print(f"URL dang chay: http://{host}:{port}")
    print("Tai khoan mac dinh (co the doi qua .env):")
    print(f"  User: {os.getenv('ADMIN_USERNAME', 'admin')} | Pass: {os.getenv('ADMIN_PASSWORD', 'admin123')}")
    print("Nhan Ctrl+C de dung")
    try:
        app.run(debug=app.config.get('DEBUG', False), host=host, port=port)
    except OSError as e:
        # Common case: port in use
        if "Address already in use" in str(e):
            alt_port = 5050
            print(f"Cong {port} dang duoc su dung. Thu chay lai voi cong {alt_port} ...")
            app.run(debug=app.config.get('DEBUG', False), host=host, port=alt_port)
        else:
            raise
