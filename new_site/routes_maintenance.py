from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from . import db
from .models import MaintenanceRecord, Asset

maint_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')


def login_required():
    return 'user_id' in session


@maint_bp.route('/')
def list_maintenance():
    if not login_required():
        return redirect(url_for('auth.login'))
    page = request.args.get('page', 1, type=int)
    records = MaintenanceRecord.query.order_by(MaintenanceRecord.maintenance_date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('maintenance/list.html', records=records)


@maint_bp.route('/add', methods=['GET', 'POST'])
def add_maintenance():
    if not login_required():
        return redirect(url_for('auth.login'))
    assets = Asset.query.all()
    if request.method == 'POST':
        from datetime import datetime
        asset_id = int(request.form['asset_id'])
        maintenance_date = datetime.fromisoformat(request.form.get('maintenance_date') or datetime.utcnow().date().isoformat()).date()
        mtype = request.form.get('type', 'maintenance')
        description = request.form.get('description', '')
        vendor = request.form.get('vendor', '')
        person = request.form.get('person_in_charge', '')
        cost = float(request.form.get('cost') or 0)
        next_due = request.form.get('next_due_date')
        next_due_date = datetime.fromisoformat(next_due).date() if next_due else None
        status = request.form.get('status', 'completed')
        rec = MaintenanceRecord(asset_id=asset_id, maintenance_date=maintenance_date, type=mtype,
                                 description=description, vendor=vendor, person_in_charge=person,
                                 cost=cost, next_due_date=next_due_date, status=status)
        db.session.add(rec)
        db.session.commit()
        flash('Đã thêm bảo trì', 'success')
        return redirect(url_for('maintenance.list_maintenance'))
    return render_template('maintenance/add.html', assets=assets)


