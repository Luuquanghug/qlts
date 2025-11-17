from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from . import db
from .models import AssetType, AuditLog

types_bp = Blueprint('types', __name__, url_prefix='/types')


def login_required():
    return 'user_id' in session


@types_bp.route('/')
def list_types():
    if not login_required():
        return redirect(url_for('auth.login'))
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '', type=str)
    query = AssetType.query
    if q:
        query = query.filter(AssetType.name.ilike(f'%{q}%'))
    items = query.order_by(AssetType.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('asset_types/list.html', items=items, q=q)


@types_bp.route('/add', methods=['GET', 'POST'])
def add_type():
    if not login_required():
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '')
        if not name:
            flash('Tên loại không được trống', 'error')
            return render_template('asset_types/add.html')
        if AssetType.query.filter_by(name=name).first():
            flash('Tên loại đã tồn tại', 'error')
            return render_template('asset_types/add.html')
        t = AssetType(name=name, description=description)
        db.session.add(t)
        db.session.commit()
        try:
            uid = session.get('user_id')
            db.session.add(AuditLog(user_id=uid, module='asset_types', action='create', entity_id=t.id, details=f'name={t.name}'))
            db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Đã thêm loại tài sản', 'success')
        return redirect(url_for('types.list_types'))
    return render_template('asset_types/add.html')


