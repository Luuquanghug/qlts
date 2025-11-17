from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from . import db
from .models import Asset, AssetType, AuditLog

assets_bp = Blueprint('assets', __name__, url_prefix='/assets')


def login_required():
    return 'user_id' in session


@assets_bp.route('/')
def list_assets():
    if not login_required():
        return redirect(url_for('auth.login'))
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '', type=str)
    query = Asset.query
    if q:
        query = query.filter(Asset.name.ilike(f'%{q}%'))
    assets = query.order_by(Asset.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('assets/list.html', assets=assets, q=q)


@assets_bp.route('/add', methods=['GET', 'POST'])
def add_asset():
    if not login_required():
        return redirect(url_for('auth.login'))
    types = AssetType.query.all()
    if request.method == 'POST':
        name = request.form['name'].strip()
        price = float(request.form.get('price') or 0)
        quantity = int(request.form.get('quantity') or 1)
        asset_type_id = int(request.form['asset_type_id'])
        status = request.form.get('status', 'active')
        notes = request.form.get('notes', '')
        if not name:
            flash('Tên tài sản không được trống', 'error')
            return render_template('assets/add.html', types=types)
        if Asset.query.filter_by(name=name).first():
            flash('Tên tài sản đã tồn tại', 'error')
            return render_template('assets/add.html', types=types)
        a = Asset(name=name, price=price, quantity=quantity, asset_type_id=asset_type_id, status=status, notes=notes)
        db.session.add(a)
        db.session.commit()
        try:
            uid = session.get('user_id')
            db.session.add(AuditLog(user_id=uid, module='assets', action='create', entity_id=a.id, details=f'name={a.name}'))
            db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Đã thêm tài sản', 'success')
        return redirect(url_for('assets.list_assets'))
    return render_template('assets/add.html', types=types)


