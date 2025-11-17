from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role')
    last_login = db.Column(db.DateTime)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class AssetType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    price = db.Column(db.Float, default=0)
    quantity = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default='active')
    notes = db.Column(db.Text)
    asset_type_id = db.Column(db.Integer, db.ForeignKey('asset_type.id'))
    asset_type = db.relationship('AssetType')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    asset = db.relationship('Asset')
    maintenance_date = db.Column(db.Date)
    type = db.Column(db.String(50))
    description = db.Column(db.String(255))
    vendor = db.Column(db.String(120))
    person_in_charge = db.Column(db.String(120))
    cost = db.Column(db.Float, default=0)
    next_due_date = db.Column(db.Date)
    status = db.Column(db.String(50))


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    module = db.Column(db.String(50))
    action = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


