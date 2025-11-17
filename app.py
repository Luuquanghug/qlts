from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
from functools import wraps
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# If using SQLite, proactively ensure the target directory exists
try:
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI') or ''
    # Print masked DB URI for easier troubleshooting (no secrets)
    try:
        masked = db_uri
        if '@' in db_uri and '://' in db_uri:
            scheme, rest = db_uri.split('://', 1)
            if ':' in rest and '@' in rest:
                head, tail = rest.split('@', 1)
                user = head.split(':', 1)[0]
                masked = f"{scheme}://{user}:***@{tail}"
        print(f"[Config] SQLALCHEMY_DATABASE_URI = {masked}")
    except Exception:
        pass
    # If Postgres URL provided but driver missing, try to coerce or fallback to SQLite
    if db_uri.startswith('postgresql://') or db_uri.startswith('postgres://'):
        coerced = db_uri.replace('postgres://', 'postgresql://', 1)
        try:
            import psycopg  # psycopg v3
            if '+psycopg' not in coerced:
                coerced = coerced.replace('postgresql://', 'postgresql+psycopg://', 1)
            db_uri = coerced
            app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        except Exception:
            try:
                import psycopg2  # legacy driver
                # ok to keep postgresql:// with psycopg2
                # Test connection, fallback to SQLite if connection fails
                try:
                    from sqlalchemy import create_engine
                    test_engine = create_engine(db_uri, pool_pre_ping=True)
                    with test_engine.connect() as conn:
                        pass  # Connection successful
                except Exception as conn_err:
                    # Connection failed, fallback to SQLite
                    fallback = 'sqlite:///./instance/app.db'
                    print(f'[Config] PostgreSQL connection failed: {conn_err}')
                    print(f'[Config] Falling back to SQLite: {fallback}')
                    app.config['SQLALCHEMY_DATABASE_URI'] = fallback
                    db_uri = fallback
            except Exception:
                # Fallback to SQLite to allow app to start
                fallback = 'sqlite:///./instance/app.db'
                print('[Config] psycopg driver not found; falling back to', fallback)
                app.config['SQLALCHEMY_DATABASE_URI'] = fallback
                db_uri = fallback
    if db_uri.startswith('sqlite:///'):
        # Support relative and absolute sqlite paths
        import pathlib
        path_part = db_uri.replace('sqlite:///', '', 1)
        db_path = pathlib.Path(path_part)
        if not db_path.is_absolute():
            # resolve relative to project root
            base_dir = pathlib.Path(__file__).resolve().parent
            db_path = (base_dir / db_path).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_sqlite_uri = f"sqlite:///{db_path}"
        app.config['SQLALCHEMY_DATABASE_URI'] = normalized_sqlite_uri
        db_uri = normalized_sqlite_uri
except Exception:
    # Non-fatal: proceed and let SQLAlchemy raise if anything else is wrong
    pass

# Import db from models
from models import db
db.init_app(app)
migrate = Migrate(app, db)

# Import models after db is initialized
from models import Asset, Role, User, AssetType, AuditLog, MaintenanceRecord

# Lightweight health endpoint (no auth) to verify server and routing are up
@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({'status': 'ok'}), 200

# Quick diagnostics (no secrets), helps verify DB connectivity and basic models
@app.route('/dev/diag')
def dev_diag():
    try:
        role_count = Role.query.count()
        user_count = User.query.count()
        asset_type_count = AssetType.query.count()
        asset_count = Asset.query.count()
        maint_count = MaintenanceRecord.query.count()
        return jsonify({
            'ok': True,
            'db_uri': ('sqlite' if app.config.get('SQLALCHEMY_DATABASE_URI','').startswith('sqlite') else 'non-sqlite'),
            'counts': {
                'roles': role_count,
                'users': user_count,
                'asset_types': asset_type_count,
                'assets': asset_count,
                'maintenance': maint_count
            }
        }), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# First-run bootstrap: create roles and an admin account without requiring login.
# Protected by optional INIT_TOKEN; if INIT_TOKEN is set in .env, the same token
# must be provided via querystring (?token=...). Safe to run multiple times (idempotent).
@app.route('/dev/bootstrap')
def dev_bootstrap():
    token_cfg = app.config.get('INIT_TOKEN') or ''
    token_req = request.args.get('token', '')
    if token_cfg and token_req != token_cfg:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    # Create base roles if missing
    created = {'roles': 0, 'users': 0}
    if Role.query.count() == 0:
        roles = [
            Role(name='admin', description='Quản trị'),
            Role(name='manager', description='Quản lý'),
            Role(name='user', description='Nhân viên'),
        ]
        db.session.add_all(roles)
        db.session.commit()
        created['roles'] = len(roles)
    # Create admin user if missing
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
        created['users'] = 1
    return jsonify({'success': True, 'created': created}), 200

# Friendly minimal error handlers to avoid blank pages
@app.errorhandler(404)
def not_found(e):
    # Keep it simple to avoid template dependency
    return ('Trang không tồn tại (404). '
            'Hãy quay lại /login hoặc /. '
            'Nếu bạn vừa click một liên kết trong giao diện, vui lòng báo lại đường dẫn.'), 404

@app.errorhandler(500)
def internal_error(e):
    return ('Lỗi máy chủ (500). Vui lòng thử lại, hoặc truy cập /dev/diag để chẩn đoán nhanh.'), 500

# Jinja filter for Vietnamese date formatting
@app.template_filter('vn_date')
def vn_date(value, include_time: bool = False):
    try:
        if value is None:
            return ''
        # Accept date or datetime
        if hasattr(value, 'strftime'):
            if include_time:
                return value.strftime('%d/%m/%Y %H:%M')
            return value.strftime('%d/%m/%Y')
        return str(value)
    except Exception:
        return ''

@app.template_filter('maintenance_status_vi')
def maintenance_status_vi(value: str):
    mapping = {
        'completed': 'Hoàn thành',
        'scheduled': 'Đã lên lịch',
        'in_progress': 'Đang thực hiện',
        'cancelled': 'Đã hủy'
    }
    key = (value or '').lower()
    return mapping.get(key, value or '')

@app.template_filter('maintenance_type_vi')
def maintenance_type_vi(value: str):
    mapping = {
        'maintenance': 'Bảo trì định kỳ',
        'repair': 'Sửa chữa',
        'inspection': 'Kiểm tra',
        'upgrade': 'Nâng cấp',
        'replacement': 'Thay thế'
    }
    key = (value or '').lower()
    return mapping.get(key, value or '')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Login routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    # i18n strings (vi/en) for login page
    lang = session.get('lang', 'vi')
    i18n = {
        'vi': {
            'title': 'Đăng nhập',
            'subtitle': 'Chào mừng bạn trở lại! Vui lòng đăng nhập để tiếp tục',
            'username': 'Tài khoản',
            'password': 'Mật khẩu',
            'remember': 'Ghi nhớ đăng nhập',
            'login': 'Đăng nhập'
        },
        'en': {
            'title': 'Sign in',
            'subtitle': 'Welcome back! Please sign in to continue',
            'username': 'Username',
            'password': 'Password',
            'remember': 'Remember me',
            'login': 'Sign in'
        }
    }[lang]
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role.name
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Chào mừng {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'error')
    
    return render_template('auth/login.html', i18n=i18n, lang=lang)

@app.route('/set-lang/<lang>')
def set_lang(lang: str):
    if lang not in ['vi', 'en']:
        lang = 'vi'
    session['lang'] = lang
    # redirect back to login or referrer
    return redirect(request.referrer or url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Bạn đã đăng xuất thành công!', 'info')
    return redirect(url_for('login'))

@app.route('/trash')
@login_required
def trash():
    """Thùng rác - hiển thị các bản ghi đã xóa mềm"""
    module = request.args.get('module', 'all')
    assets = Asset.query.filter(Asset.deleted_at.isnot(None)).all()
    asset_types = AssetType.query.filter(AssetType.deleted_at.isnot(None)).all()
    users = User.query.filter(User.deleted_at.isnot(None)).all()
    maintenance_records = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.isnot(None)).all()
    return render_template(
        'trash/list.html',
        module=module,
        assets=assets,
        asset_types=asset_types,
        users=users,
        maintenance_records=maintenance_records
    )

@app.route('/trash/restore', methods=['POST'])
@login_required
def trash_restore():
    """Khôi phục bản ghi đã xóa mềm"""
    module = request.form.get('module') or request.args.get('module')
    id_str = request.form.get('id') or request.args.get('id')
    try:
        entity_id = int(id_str)
    except Exception:
        flash('Yêu cầu không hợp lệ.', 'error')
        return redirect(url_for('trash', module=module or 'all'))
    model_map = {
        'asset': Asset,
        'asset_type': AssetType,
        'user': User,
        'maintenance': MaintenanceRecord
    }
    model = model_map.get(module)
    if not model:
        flash('Phân hệ không hợp lệ.', 'error')
        return redirect(url_for('trash', module='all'))
    obj = model.query.get(entity_id)
    if not obj:
        flash('Không tìm thấy bản ghi.', 'error')
        return redirect(url_for('trash', module=module))
    if hasattr(obj, 'restore'):
        obj.restore()
        db.session.commit()
        flash('Khôi phục thành công.', 'success')
    else:
        flash('Bản ghi không hỗ trợ khôi phục.', 'error')
    return redirect(url_for('trash', module=module))

@app.route('/trash/permanent-delete', methods=['POST'])
@login_required
def trash_permanent_delete():
    """Xóa vĩnh viễn bản ghi"""
    module = request.form.get('module') or request.args.get('module')
    id_str = request.form.get('id') or request.args.get('id')
    try:
        entity_id = int(id_str)
    except Exception:
        flash('Yêu cầu không hợp lệ.', 'error')
        return redirect(url_for('trash', module=module or 'all'))
    model_map = {
        'asset': Asset,
        'asset_type': AssetType,
        'user': User,
        'maintenance': MaintenanceRecord
    }
    model = model_map.get(module)
    if not model:
        flash('Phân hệ không hợp lệ.', 'error')
        return redirect(url_for('trash', module='all'))
    obj = model.query.get(entity_id)
    if not obj:
        flash('Không tìm thấy bản ghi.', 'error')
        return redirect(url_for('trash', module=module))
    db.session.delete(obj)
    db.session.commit()
    flash('Đã xóa vĩnh viễn.', 'success')
    return redirect(url_for('trash', module=module))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    assets = Asset.query.all()
    asset_types = AssetType.query.all()
    users = User.query.all()
    
    stats = {
        'total_assets': len(assets),
        'total_asset_types': len(asset_types),
        'total_users': len(users),
        'active_assets': len([a for a in assets if a.status == 'active'])
    }
    
    # Auto schedule yearly maintenance and show due soon list
    from datetime import timedelta
    today = datetime.utcnow().date()

    # Ensure each asset has a next scheduled maintenance (yearly)
    for a in assets:
        last = MaintenanceRecord.query.filter_by(asset_id=a.id).order_by(MaintenanceRecord.next_due_date.desc()).first()
        next_due = None
        if last and last.next_due_date:
            next_due = last.next_due_date
        # if no future schedule, create one a year from today or from last due date passed
        need_create = False
        if not next_due:
            need_create = True
        elif next_due < today:
            need_create = True
        if need_create:
            try:
                rec = MaintenanceRecord(
                    asset_id=a.id,
                    maintenance_date=today,
                    type='maintenance',
                    description='Lịch bảo trì định kỳ (tự động)',
                    vendor=None,
                    person_in_charge='System',
                    cost=0,
                    next_due_date=today + timedelta(days=365),
                    status='scheduled'
                )
                db.session.add(rec)
            except Exception:
                db.session.rollback()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Due soon/overdue notifications and list (30 days window)
    due_window = today + timedelta(days=30)
    due_records = MaintenanceRecord.query\
        .filter(MaintenanceRecord.next_due_date != None, MaintenanceRecord.next_due_date <= due_window)\
        .order_by(MaintenanceRecord.next_due_date.asc())\
        .limit(10).all()

    overdue = sum(1 for r in due_records if r.next_due_date < today)
    due_soon = sum(1 for r in due_records if r.next_due_date >= today)
    if overdue:
        flash(f'{overdue} thiết bị quá hạn bảo trì!', 'warning')
    elif due_soon:
        flash(f'{due_soon} thiết bị sắp đến hạn bảo trì trong 30 ngày.', 'info')

    return render_template('index.html', assets=assets, stats=stats, asset_types=asset_types, due_records=due_records, today=today)

@app.route('/assets')
@login_required
def assets():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    type_id = request.args.get('type_id', type=int)
    status = request.args.get('status', type=str)

    query = Asset.query
    if search:
        query = query.filter(Asset.name.ilike(f'%{search}%'))
    if type_id:
        query = query.filter(Asset.asset_type_id == type_id)
    if status:
        query = query.filter(Asset.status == status)

    assets = query.paginate(page=page, per_page=10, error_out=False)
    asset_types = AssetType.query.all()
    return render_template('assets/list.html', assets=assets, asset_types=asset_types, search=search, type_id=type_id, status=status)

@app.route('/assets/export/<string:fmt>')
@login_required
def export_assets(fmt: str):
    fmt = (fmt or '').lower()
    # Common, normalized dataset
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).order_by(Asset.id.asc()).all()
    rows = []
    for a in assets:
        rows.append({
            'id': a.id,
            'name': a.name,
            'asset_type': a.asset_type.name if a.asset_type else '',
            'price': float(a.price or 0),
            'quantity': int(a.quantity or 0),
            'purchase_date': a.purchase_date.strftime('%d/%m/%Y') if a.purchase_date else '',
            'device_code': a.device_code or '',
            'user': a.user.username if a.user else '',
            'condition': a.condition_label or '',
            'status': a.status or '',
            'notes': a.notes or ''
        })
    headers_vi = {
        'id': 'ID',
        'name': 'Tên tài sản',
        'asset_type': 'Loại',
        'price': 'Giá',
        'quantity': 'Số lượng',
        'purchase_date': 'Ngày mua',
        'device_code': 'Mã thiết bị',
        'user': 'Người sử dụng',
        'condition': 'Tình trạng',
        'status': 'Trạng thái',
        'notes': 'Ghi chú'
    }
    ordered_fields = list(headers_vi.keys())

    def _save_and_response(data_bytes: bytes, filename: str, content_type: str):
        # Persist a copy to EXPORT_DIR
        try:
            export_dir = app.config.get('EXPORT_DIR', 'instance/exports')
            # Normalize to absolute path relative to app.root_path if needed
            if not os.path.isabs(export_dir):
                export_dir = os.path.join(app.root_path, export_dir)
            os.makedirs(export_dir, exist_ok=True)
            ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            base, ext = os.path.splitext(filename)
            server_filename = f"{base}_{ts}{ext}"
            out_path = os.path.join(export_dir, server_filename)
            with open(out_path, 'wb') as f:
                f.write(data_bytes)
        except Exception:
            # Non-fatal: logging to console; still return download
            print('[Export] Failed to persist exported file to disk.')
        response = make_response(data_bytes)
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Content-Type'] = content_type
        return response

    if fmt == 'csv':
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([headers_vi[f] for f in ordered_fields])
        for r in rows:
            writer.writerow([r[f] for f in ordered_fields])
        csv_data = output.getvalue().encode('utf-8-sig')
        return _save_and_response(csv_data, 'tai_san.csv', 'text/csv; charset=utf-8')
    elif fmt in ('xlsx', 'excel'):
        # Use pandas/openpyxl
        import pandas as pd  # type: ignore
        from io import BytesIO
        df = pd.DataFrame(rows, columns=ordered_fields)
        df.columns = [headers_vi[f] for f in ordered_fields]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='TaiSan')
        buf.seek(0)
        data = buf.read()
        return _save_and_response(data, 'tai_san.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    elif fmt == 'json':
        import json
        data = json.dumps(rows, ensure_ascii=False).encode('utf-8')
        return _save_and_response(data, 'tai_san.json', 'application/json; charset=utf-8')
    elif fmt == 'docx':
        # Use utils.exporters for Word
        from types import SimpleNamespace
        from utils.exporters import export_docx
        ns_rows = [SimpleNamespace(**r) for r in rows]
        buf = export_docx(ns_rows, ordered_fields, title='Danh sách tài sản', header_map=headers_vi)
        return _save_and_response(buf.getvalue(), 'tai_san.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    elif fmt == 'pdf':
        # Use utils.exporters for PDF
        from types import SimpleNamespace
        from utils.exporters import export_pdf
        ns_rows = [SimpleNamespace(**r) for r in rows]
        buf = export_pdf(ns_rows, ordered_fields, title='Danh sách tài sản', header_map=headers_vi)
        return _save_and_response(buf.getvalue(), 'tai_san.pdf', 'application/pdf')
    else:
        flash('Định dạng không được hỗ trợ. Hỗ trợ: csv, xlsx, json, docx, pdf.', 'warning')
        return redirect(url_for('assets'))

# Maintenance module
@app.route('/maintenance')
@login_required
def maintenance_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    asset_id = request.args.get('asset_id', type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    overdue_flag = request.args.get('overdue', type=int)
    due30_flag = request.args.get('due_30', type=int)

    query = MaintenanceRecord.query
    if asset_id:
        query = query.filter(MaintenanceRecord.asset_id == asset_id)
    if search:
        like = f'%{search}%'
        query = query.filter((MaintenanceRecord.description.ilike(like)) | (MaintenanceRecord.vendor.ilike(like)) | (MaintenanceRecord.person_in_charge.ilike(like)))
    if month:
        query = query.filter(db.extract('month', MaintenanceRecord.maintenance_date) == month)
    if year:
        query = query.filter(db.extract('year', MaintenanceRecord.maintenance_date) == year)
    # Additional filters for next due date
    if overdue_flag:
        today = datetime.utcnow().date()
        query = query.filter(MaintenanceRecord.next_due_date != None, MaintenanceRecord.next_due_date < today)
    if due30_flag:
        from datetime import timedelta
        today = datetime.utcnow().date()
        query = query.filter(
            MaintenanceRecord.next_due_date != None,
            MaintenanceRecord.next_due_date.between(today, today + timedelta(days=30))
        )

    records = query.order_by(MaintenanceRecord.maintenance_date.desc()).paginate(page=page, per_page=10, error_out=False)
    assets = Asset.query.all()
    return render_template(
        'maintenance/list.html',
        records=records,
        assets=assets,
        search=search,
        asset_id=asset_id,
        month=month,
        year=year,
        overdue=overdue_flag,
        due_30=due30_flag
    )

@app.route('/maintenance/add', methods=['GET','POST'])
@login_required
def maintenance_add():
    if request.method == 'POST':
        asset_id = int(request.form['asset_id'])
        maintenance_date = request.form.get('maintenance_date') or datetime.utcnow().date().isoformat()
        mtype = request.form.get('type','maintenance')
        description = request.form.get('description','')
        vendor = request.form.get('vendor','')
        person = request.form.get('person_in_charge','')
        cost = float(request.form.get('cost', 0) or 0)
        next_due_date = request.form.get('next_due_date') or None
        status_val = request.form.get('status','completed')

        rec = MaintenanceRecord(
            asset_id=asset_id,
            maintenance_date=datetime.fromisoformat(maintenance_date).date(),
            type=mtype,
            description=description,
            vendor=vendor,
            person_in_charge=person,
            cost=cost,
            next_due_date=datetime.fromisoformat(next_due_date).date() if next_due_date else None,
            status=status_val
        )
        db.session.add(rec)
        db.session.commit()
        flash('Đã ghi nhận bảo trì/sửa chữa.', 'success')
        return redirect(url_for('maintenance_list'))
    assets = Asset.query.all()
    return render_template('maintenance/add.html', assets=assets)

@app.route('/maintenance/edit/<int:id>', methods=['GET','POST'])
@login_required
def maintenance_edit(id):
    rec = MaintenanceRecord.query.get_or_404(id)
    if request.method == 'POST':
        rec.asset_id = int(request.form['asset_id'])
        maintenance_date = request.form.get('maintenance_date') or datetime.utcnow().date().isoformat()
        rec.maintenance_date = datetime.fromisoformat(maintenance_date).date()
        rec.type = request.form.get('type','maintenance')
        rec.description = request.form.get('description','')
        rec.vendor = request.form.get('vendor','')
        rec.person_in_charge = request.form.get('person_in_charge','')
        rec.cost = float(request.form.get('cost', 0) or 0)
        next_due_date = request.form.get('next_due_date') or None
        rec.next_due_date = datetime.fromisoformat(next_due_date).date() if next_due_date else None
        rec.status = request.form.get('status','completed')
        db.session.commit()
        flash('Đã cập nhật bản ghi bảo trì.', 'success')
        return redirect(url_for('maintenance_list'))
    assets = Asset.query.all()
    return render_template('maintenance/edit.html', rec=rec, assets=assets)

@app.route('/maintenance/view/<int:id>')
@login_required
def maintenance_view(id):
    rec = MaintenanceRecord.query.get_or_404(id)
    return render_template('maintenance/view.html', rec=rec)

@app.route('/maintenance/delete/<int:id>')
@login_required
def maintenance_delete(id):
    rec = MaintenanceRecord.query.get_or_404(id)
    db.session.delete(rec)
    db.session.commit()
    flash('Đã xóa bản ghi bảo trì.', 'success')
    return redirect(url_for('maintenance_list'))

@app.route('/maintenance/report')
@login_required
def maintenance_report():
    # Simple aggregation by month/year
    year = request.args.get('year', type=int)
    if not year:
        year = datetime.utcnow().year
    rows = db.session.query(
        db.extract('month', MaintenanceRecord.maintenance_date).label('month'),
        db.func.sum(MaintenanceRecord.cost).label('total')
    ).filter(db.extract('year', MaintenanceRecord.maintenance_date) == year)
    rows = rows.group_by('month').order_by('month').all()
    data = [{'month': int(r.month), 'total': float(r.total or 0)} for r in rows]
    total_year = sum(d['total'] for d in data)
    return render_template('maintenance/report.html', year=year, data=data, total_year=total_year)

@app.route('/maintenance/dashboard')
@login_required
def maintenance_dashboard():
    from datetime import timedelta, date
    today = datetime.utcnow().date()
    year = today.year
    month = today.month
    # KPIs (avoid db.extract for SQLite compatibility)
    start_year = date(year, 1, 1)
    end_year = date(year, 12, 31)
    total_records_year = MaintenanceRecord.query \
        .filter(MaintenanceRecord.maintenance_date >= start_year, MaintenanceRecord.maintenance_date <= end_year).count()
    total_cost_year = db.session.query(db.func.sum(MaintenanceRecord.cost)) \
        .filter(MaintenanceRecord.maintenance_date >= start_year, MaintenanceRecord.maintenance_date <= end_year).scalar() or 0
    # Detailed year stats
    year_records = MaintenanceRecord.query \
        .filter(MaintenanceRecord.maintenance_date >= start_year, MaintenanceRecord.maintenance_date <= end_year).all()
    completed_year = sum(1 for r in year_records if (r.status or '').lower() == 'completed')
    scheduled_year = sum(1 for r in year_records if (r.status or '').lower() == 'scheduled')
    in_progress_year = sum(1 for r in year_records if (r.status or '').lower() == 'in_progress')
    cancelled_year = sum(1 for r in year_records if (r.status or '').lower() == 'cancelled')
    records_with_cost_year = sum(1 for r in year_records if (r.cost or 0) > 0)
    costs_year = [float(r.cost or 0) for r in year_records if (r.cost or 0) > 0]
    max_cost_year = max(costs_year) if costs_year else 0
    min_cost_year = min(costs_year) if costs_year else 0
    completion_rate = round((completed_year / total_records_year) * 100, 1) if total_records_year else 0
    avg_cost_per_record = round(total_cost_year / total_records_year) if total_records_year else 0
    # Month stats (current month)
    start_month = date(year, month, 1)
    # Compute end of month safely
    if month == 12:
        start_next_month = date(year + 1, 1, 1)
    else:
        start_next_month = date(year, month + 1, 1)
    end_month = start_next_month - timedelta(days=1)
    month_records = MaintenanceRecord.query \
        .filter(MaintenanceRecord.maintenance_date >= start_month, MaintenanceRecord.maintenance_date <= end_month).all()
    total_records_month = len(month_records)
    total_cost_month = sum(float(r.cost or 0) for r in month_records)
    records_with_cost_month = sum(1 for r in month_records if (r.cost or 0) > 0)
    costs_month = [float(r.cost or 0) for r in month_records if (r.cost or 0) > 0]
    max_cost_month = max(costs_month) if costs_month else 0
    min_cost_month = min(costs_month) if costs_month else 0
    completed_month = sum(1 for r in month_records if (r.status or '').lower() == 'completed')
    in_progress_month = sum(1 for r in month_records if (r.status or '').lower() == 'in_progress')
    # Overdue lists and counts
    overdue = MaintenanceRecord.query\
        .filter(MaintenanceRecord.next_due_date != None, MaintenanceRecord.next_due_date < today).count()
    overdue_records = MaintenanceRecord.query\
        .filter(MaintenanceRecord.next_due_date != None, MaintenanceRecord.next_due_date < today)\
        .order_by(MaintenanceRecord.next_due_date.asc()).limit(10).all()
    due_30 = MaintenanceRecord.query\
        .filter(MaintenanceRecord.next_due_date != None, MaintenanceRecord.next_due_date.between(today, today + timedelta(days=30))).count()

    # Recent / upcoming
    recent = MaintenanceRecord.query.order_by(MaintenanceRecord.maintenance_date.desc()).limit(8).all()
    upcoming = MaintenanceRecord.query \
        .filter(
            MaintenanceRecord.next_due_date != None,
            MaintenanceRecord.next_due_date.between(today, today + timedelta(days=30))
        ) \
        .order_by(MaintenanceRecord.next_due_date.asc()).all()

    return render_template('maintenance/dashboard.html',
                           today=today,
                           year=year,
                           month=month,
                           total_records_year=total_records_year,
                           total_cost_year=total_cost_year,
                           completed_year=completed_year,
                           scheduled_year=scheduled_year,
                           in_progress_year=in_progress_year,
                           cancelled_year=cancelled_year,
                           records_with_cost_year=records_with_cost_year,
                           max_cost_year=max_cost_year,
                           min_cost_year=min_cost_year,
                           completion_rate=completion_rate,
                           avg_cost_per_record=avg_cost_per_record,
                           total_records_month=total_records_month,
                           total_cost_month=total_cost_month,
                           records_with_cost_month=records_with_cost_month,
                           max_cost_month=max_cost_month,
                           min_cost_month=min_cost_month,
                           completed_month=completed_month,
                           in_progress_month=in_progress_month,
                           overdue=overdue,
                           due_30=due_30,
                           overdue_records=overdue_records,
                           recent=recent,
                           upcoming=upcoming)

@app.route('/assets/add', methods=['GET', 'POST'])
@login_required
def add_asset():
    if request.method == 'POST':
        name = request.form['name'].strip()
        try:
            price = float(request.form['price'])
        except Exception:
            price = 0.0
        try:
            quantity = int(request.form['quantity'])
        except Exception:
            quantity = 0
        asset_type_id = request.form['asset_type_id']
        user_id = request.form.get('user_id') or None
        user_text = request.form.get('user_text', '')
        notes = request.form.get('notes', '')
        usage_months = request.form.get('usage_months')
        condition_percent = request.form.get('condition_percent')
        status = request.form['status']
        # Validate basic constraints
        if not name:
            flash('Tên tài sản không được để trống.', 'error')
            return redirect(url_for('add_asset'))
        if price <= 0:
            flash('Giá phải lớn hơn 0.', 'error')
            return redirect(url_for('add_asset'))
        if quantity < 1:
            flash('Số lượng phải >= 1.', 'error')
            return redirect(url_for('add_asset'))
        # Duplicate name (cảnh báo)
        if Asset.query.filter_by(name=name).first():
            flash('Tên tài sản đã tồn tại, vui lòng chọn tên khác.', 'error')
            return redirect(url_for('add_asset'))
        
        # Append usage/condition into notes if provided
        prefix_parts = []
        try:
            if usage_months is not None and usage_months != '':
                um = int(usage_months)
                if um < 0:
                    flash('Thời gian sử dụng không hợp lệ.', 'error')
                    return redirect(url_for('add_asset'))
                prefix_parts.append(f"Thời gian sử dụng: {um} tháng")
        except Exception:
            flash('Thời gian sử dụng không hợp lệ.', 'error')
            return redirect(url_for('add_asset'))
        try:
            if condition_percent is not None and condition_percent != '':
                cp = int(condition_percent)
                if cp < 0 or cp > 100:
                    flash('Độ mới phải trong khoảng 0-100%.', 'error')
                    return redirect(url_for('add_asset'))
                prefix_parts.append(f"Độ mới: {cp}%")
        except Exception:
            flash('Độ mới không hợp lệ.', 'error')
            return redirect(url_for('add_asset'))
        if prefix_parts:
            notes = ("; ".join(prefix_parts) + ".\n") + (notes or '')

        asset = Asset(
            name=name,
            price=price,
            quantity=quantity,
            asset_type_id=asset_type_id,
            user_id=user_id,
            user_text=user_text,
            notes=notes,
            status=status
        )
        
        db.session.add(asset)
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='assets', action='create', entity_id=asset.id, details=f"name={name}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Tài sản đã được thêm thành công!', 'success')
        return redirect(url_for('assets'))
    
    asset_types = AssetType.query.all()
    users = User.query.all()
    return render_template('assets/add.html', asset_types=asset_types, users=users)

@app.route('/assets/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_asset(id):
    asset = Asset.query.get_or_404(id)
    
    if request.method == 'POST':
        asset.name = request.form['name'].strip()
        try:
            asset.price = float(request.form['price'])
        except Exception:
            asset.price = 0.0
        try:
            asset.quantity = int(request.form['quantity'])
        except Exception:
            asset.quantity = 0
        asset.asset_type_id = request.form['asset_type_id']
        asset.user_id = request.form.get('user_id') or None
        asset.user_text = request.form.get('user_text', '')
        notes = request.form.get('notes', '')
        usage_months = request.form.get('usage_months')
        condition_percent = request.form.get('condition_percent')
        prefix_parts = []
        try:
            if usage_months is not None and usage_months != '':
                um = int(usage_months)
                if um < 0:
                    flash('Thời gian sử dụng không hợp lệ.', 'error')
                    return redirect(url_for('edit_asset', id=id))
                prefix_parts.append(f"Thời gian sử dụng: {um} tháng")
        except Exception:
            flash('Thời gian sử dụng không hợp lệ.', 'error')
            return redirect(url_for('edit_asset', id=id))
        try:
            if condition_percent is not None and condition_percent != '':
                cp = int(condition_percent)
                if cp < 0 or cp > 100:
                    flash('Độ mới phải trong khoảng 0-100%.', 'error')
                    return redirect(url_for('edit_asset', id=id))
                prefix_parts.append(f"Độ mới: {cp}%")
        except Exception:
            flash('Độ mới không hợp lệ.', 'error')
            return redirect(url_for('edit_asset', id=id))
        if prefix_parts:
            notes = ("; ".join(prefix_parts) + ".\n") + (notes or '')
        asset.notes = notes
        asset.status = request.form['status']
        # Validate
        if not asset.name:
            flash('Tên tài sản không được để trống.', 'error')
            return redirect(url_for('edit_asset', id=id))
        if asset.price <= 0:
            flash('Giá phải lớn hơn 0.', 'error')
            return redirect(url_for('edit_asset', id=id))
        if asset.quantity < 1:
            flash('Số lượng phải >= 1.', 'error')
            return redirect(url_for('edit_asset', id=id))
        dup = Asset.query.filter(Asset.name == asset.name, Asset.id != id).first()
        if dup:
            flash('Tên tài sản đã tồn tại, vui lòng chọn tên khác.', 'error')
            return redirect(url_for('edit_asset', id=id))
        
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='assets', action='update', entity_id=id, details=f"name={asset.name}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Tài sản đã được cập nhật thành công!', 'success')
        return redirect(url_for('assets'))
    
    asset_types = AssetType.query.all()
    users = User.query.all()
    return render_template('assets/edit.html', asset=asset, asset_types=asset_types, users=users)

@app.route('/assets/delete/<int:id>')
@login_required
def delete_asset(id):
    asset = Asset.query.get_or_404(id)
    db.session.delete(asset)
    db.session.commit()
    try:
        uid = session.get('user_id')
        if uid:
            db.session.add(AuditLog(user_id=uid, module='assets', action='delete', entity_id=id, details=f"name={asset.name}"))
            db.session.commit()
    except Exception:
        db.session.rollback()
    flash('Tài sản đã được xóa thành công!', 'success')
    return redirect(url_for('assets'))

@app.route('/asset-types')
@login_required
def asset_types():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = AssetType.query
    
    if search:
        query = query.filter(AssetType.name.ilike(f'%{search}%'))
    
    asset_types = query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('asset_types/list.html', 
                         asset_types=asset_types, 
                         search=search)

@app.route('/asset-types/add', methods=['POST'])
@login_required
def add_asset_type():
    try:
        name = request.form['name']
        description = request.form.get('description', '')
        
        # Kiểm tra tên đã tồn tại
        existing = AssetType.query.filter_by(name=name).first()
        if existing:
            return jsonify({'success': False, 'message': 'Tên loại tài sản đã tồn tại!'})
        
        asset_type = AssetType(name=name, description=description)
        db.session.add(asset_type)
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='asset_types', action='create', entity_id=asset_type.id, details=f"name={name}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        
        return jsonify({
            'success': True, 
            'message': 'Loại tài sản đã được thêm thành công!',
            'data': {
                'id': asset_type.id,
                'name': asset_type.name,
                'description': asset_type.description,
                'created_at': asset_type.created_at.strftime('%d/%m/%Y %H:%M')
            }
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/asset-types/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_asset_type(id):
    asset_type = AssetType.query.get_or_404(id)
    if request.method == 'GET':
        return render_template('asset_types/edit.html', asset_type=asset_type)
    try:
        name = request.form['name']
        description = request.form.get('description', '')
        # Kiểm tra tên đã tồn tại (trừ chính nó)
        existing = AssetType.query.filter(AssetType.name == name, AssetType.id != id).first()
        if existing:
            flash('Tên loại tài sản đã tồn tại!', 'error')
            return render_template('asset_types/edit.html', asset_type=asset_type)
        asset_type.name = name
        asset_type.description = description
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='asset_types', action='update', entity_id=id, details=f"name={asset_type.name}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Loại tài sản đã được cập nhật thành công!', 'success')
        return redirect(url_for('asset_types'))
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi: {str(e)}', 'error')
        return render_template('asset_types/edit.html', asset_type=asset_type)

@app.route('/asset-types/delete/<int:id>', methods=['POST'])
@login_required
def delete_asset_type(id):
    try:
        asset_type = AssetType.query.get_or_404(id)
        
        # Kiểm tra có tài sản nào đang sử dụng loại này không
        if asset_type.assets:
            return jsonify({'success': False, 'message': 'Không thể xóa loại tài sản đang được sử dụng!'})
        
        db.session.delete(asset_type)
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='asset_types', action='delete', entity_id=id, details=f"name={asset_type.name}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        
        return jsonify({'success': True, 'message': 'Loại tài sản đã được xóa thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/users')
@login_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    role_id = request.args.get('role_id', type=int)

    query = User.query
    if search:
        like = f'%{search}%'
        query = query.filter((User.username.ilike(like)) | (User.email.ilike(like)))
    if role_id:
        query = query.filter(User.role_id == role_id)

    users = query.paginate(page=page, per_page=10, error_out=False)
    roles = Role.query.all()
    return render_template('users/list.html', users=users, roles=roles, search=search, role_id=role_id)

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'GET':
        roles = Role.query.all()
        return render_template('users/edit.html', user=user, roles=roles)
    try:
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        role_id = request.form['role_id']
        password = request.form.get('password')
        is_active = True if request.form.get('is_active') == 'on' else False

        if User.query.filter(User.username == username, User.id != id).first():
            flash('Tên đăng nhập đã tồn tại!', 'error')
            roles = Role.query.all()
            return render_template('users/edit.html', user=user, roles=roles)
        if User.query.filter(User.email == email, User.id != id).first():
            flash('Email đã tồn tại!', 'error')
            roles = Role.query.all()
            return render_template('users/edit.html', user=user, roles=roles)

        import re
        email_regex = r'^([\w\.-]+)@([\w\.-]+)\.([a-zA-Z]{2,})$'
        if not re.match(email_regex, email):
            flash('Email không hợp lệ!', 'error')
            roles = Role.query.all()
            return render_template('users/edit.html', user=user, roles=roles)

        user.username = username
        user.email = email
        user.role_id = role_id
        user.is_active = is_active
        if password:
            user.set_password(password)

        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='users', action='update', entity_id=id, details=f"username={user.username}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Người dùng đã được cập nhật!', 'success')
        return redirect(url_for('users'))
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi: {str(e)}', 'error')
        roles = Role.query.all()
        return render_template('users/edit.html', user=user, roles=roles)

@app.route('/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    try:
        user = User.query.get_or_404(id)
        if user.assets:
            flash('Không thể xóa người dùng đang sở hữu tài sản!', 'error')
            return redirect(url_for('users'))
        db.session.delete(user)
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='users', action='delete', entity_id=id, details=f"username={user.username}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Đã xóa người dùng!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi: {str(e)}', 'error')
    return redirect(url_for('users'))

@app.route('/audit-logs')
@login_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    search_user = request.args.get('user_id', type=int)
    module = request.args.get('module', '', type=str)
    date_from = request.args.get('date_from', '', type=str)
    date_to = request.args.get('date_to', '', type=str)

    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    if search_user:
        query = query.filter(AuditLog.user_id == search_user)
    if module:
        query = query.filter(AuditLog.module == module)
    try:
        if date_from:
            start = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at >= start)
        if date_to:
            end = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(AuditLog.created_at <= end)
    except Exception:
        pass

    logs = query.paginate(page=page, per_page=10, error_out=False)
    users = User.query.all()
    modules = ['assets', 'asset_types', 'users']
    return render_template('audit_logs/list.html', logs=logs, users=users, modules=modules,
                           search_user=search_user, module=module, date_from=date_from, date_to=date_to)

@app.route('/test-session')
@login_required
def test_session():
    return jsonify({
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
    })

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        role_id = request.form['role_id']
        # Validate
        if not username:
            flash('Tên đăng nhập không được để trống.', 'error')
            return redirect(url_for('add_user'))
        import re
        email_regex = r'^([\w\.-]+)@([\w\.-]+)\.([a-zA-Z]{2,})$'
        if not re.match(email_regex, email):
            flash('Email không hợp lệ.', 'error')
            return redirect(url_for('add_user'))
        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại.', 'error')
            return redirect(url_for('add_user'))
        if User.query.filter_by(email=email).first():
            flash('Email đã tồn tại.', 'error')
            return redirect(url_for('add_user'))
        
        user = User(
            username=username,
            email=email,
            role_id=role_id
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='users', action='create', entity_id=user.id, details=f"username={username}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Người dùng đã được thêm thành công!', 'success')
        return redirect(url_for('users'))
    
    roles = Role.query.all()
    return render_template('users/add.html', roles=roles)

@app.route('/dev/seed-sample')
@login_required
def seed_sample():
    # Optional: restrict to admin
    if session.get('role') != 'admin':
        flash('Chỉ admin mới được phép thực hiện.', 'error')
        return redirect(url_for('index'))

    # Ensure base roles
    if Role.query.count() == 0:
        roles = [
            Role(name='admin', description='Quản trị'),
            Role(name='manager', description='Quản lý'),
            Role(name='user', description='Nhân viên'),
        ]
        db.session.add_all(roles)
        db.session.commit()

    # Seed users up to at least 25
    base_users = [
        ('user', 'user', 'user{}@example.com', 3),
        ('manager', 'manager', 'manager{}@example.com', 2)
    ]
    current_users = User.query.count()
    idx = 1
    while current_users < 25 and idx <= 30:
        for prefix, pwd, email_tpl, role_id in base_users:
            if current_users >= 25:
                break
            username = f"{prefix}{idx}"
            if not User.query.filter_by(username=username).first():
                u = User(username=username, email=email_tpl.format(idx), role_id=role_id, is_active=True)
                u.set_password(pwd + '123')
                db.session.add(u)
                current_users += 1
        idx += 1
    db.session.commit()

    # Seed asset types up to at least 12
    default_types = [
        'Máy tính', 'Thiết bị văn phòng', 'Nội thất', 'Thiết bị mạng', 'Điện thoại',
        'Thiết bị điện', 'Phần mềm', 'Thiết bị an ninh', 'Dụng cụ', 'Khác'
    ]
    for name in default_types:
        if not AssetType.query.filter_by(name=name).first():
            db.session.add(AssetType(name=name, description=f'{name} - mẫu'))
    db.session.commit()

    # Seed assets up to at least 60
    import random
    types = AssetType.query.all()
    users = User.query.all()
    current_assets = Asset.query.count()
    while current_assets < 60:
        t = random.choice(types)
        owner = random.choice(users) if users else None
        a = Asset(
            name=f"TS-{current_assets+1:03d}",
            price=random.randint(500_000, 50_000_000),
            quantity=random.randint(1, 10),
            asset_type_id=t.id,
            user_id=owner.id if owner else None,
            status=random.choice(['active', 'maintenance', 'disposed'])
        )
        db.session.add(a)
        current_assets += 1
    db.session.commit()

    flash('Đã thêm dữ liệu mẫu cho phân trang.', 'success')
    return redirect(url_for('index'))

@app.route('/dev/seed-maintenance')
@login_required
def seed_maintenance():
    if session.get('role') != 'admin':
        flash('Chỉ admin mới được phép thực hiện.', 'error')
        return redirect(url_for('maintenance_list'))
    import random
    from datetime import timedelta
    assets = Asset.query.limit(20).all()
    if not assets:
        flash('Chưa có tài sản để tạo bảo trì mẫu.', 'error')
        return redirect(url_for('maintenance_list'))
    created = 0
    today = datetime.utcnow().date()
    for i in range(10):
        a = random.choice(assets)
        days_ago = random.randint(0, 180)
        mdate = today - timedelta(days=days_ago)
        next_due = mdate + timedelta(days=random.choice([30,60,90]))
        rec = MaintenanceRecord(
            asset_id=a.id,
            maintenance_date=mdate,
            type=random.choice(['maintenance','repair','inspection']),
            description=f'Bảo trì mẫu #{i+1} cho {a.name}',
            vendor=random.choice(['FPT Services','Viettel','NCC A','NCC B']),
            person_in_charge=random.choice(['Admin','Kỹ thuật 1','Kỹ thuật 2']),
            cost=random.randint(100_000, 5_000_000),
            next_due_date=next_due,
            status='completed'
        )
        db.session.add(rec)
        created += 1
    db.session.commit()
    flash(f'Đã tạo {created} bản ghi bảo trì mẫu.', 'success')
    return redirect(url_for('maintenance_list'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=app.config.get('DEBUG', False))
