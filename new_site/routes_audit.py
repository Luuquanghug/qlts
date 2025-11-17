from flask import Blueprint, render_template, request, redirect, url_for, session
from .models import AuditLog, User

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')


def login_required():
    return 'user_id' in session


@audit_bp.route('/')
def list_audit():
    if not login_required():
        return redirect(url_for('auth.login'))
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    users = User.query.all()
    return render_template('audit/list.html', logs=logs, users=users)


