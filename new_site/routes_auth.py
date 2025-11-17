from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from . import db
from .models import User, Role

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role.name if user.role else 'user'
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('index'))
        flash('Sai tài khoản hoặc mật khẩu', 'error')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dev/seed')
def dev_seed():
    # Create basic roles and an admin user if not exist
    if Role.query.count() == 0:
        db.session.add_all([
            Role(name='admin', description='Quản trị'),
            Role(name='manager', description='Quản lý'),
            Role(name='user', description='Nhân viên'),
        ])
        db.session.commit()
    if User.query.filter_by(username='admin').first() is None:
        admin_role = Role.query.filter_by(name='admin').first()
        u = User(username='admin', email='admin@example.com', role_id=admin_role.id, is_active=True)
        u.set_password('admin123')
        db.session.add(u)
        db.session.commit()
    flash('Đã khởi tạo dữ liệu mẫu. Tài khoản: admin/admin123', 'success')
    return redirect(url_for('auth.login'))


