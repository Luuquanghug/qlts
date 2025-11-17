from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association table for many-to-many assignments between assets and users
asset_user = db.Table(
    'asset_user',
    db.Column('asset_id', db.Integer, db.ForeignKey('asset.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    users = db.relationship('User', backref='role', lazy=True)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationship
    # Owner relationship (legacy single owner)
    assets = db.relationship('Asset', backref='user', lazy=True)
    # Assigned assets (many-to-many)
    assigned_assets = db.relationship(
        'Asset',
        secondary=asset_user,
        back_populates='assigned_users',
        lazy='subquery'
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def soft_delete(self):
        """Soft delete user"""
        self.deleted_at = datetime.utcnow()
        self.is_active = False
    
    def restore(self):
        """Restore deleted user"""
        self.deleted_at = None
        self.is_active = True
    
    def __repr__(self):
        return f'<User {self.username}>'

class AssetType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    assets = db.relationship('Asset', backref='asset_type', lazy=True)
    
    def soft_delete(self):
        """Soft delete asset type"""
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restore deleted asset type"""
        self.deleted_at = None
    
    def __repr__(self):
        return f'<AssetType {self.name}>'

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='active')  # active, maintenance, disposed
    # New optional fields
    purchase_date = db.Column(db.Date, nullable=True)
    device_code = db.Column(db.String(100), nullable=True)
    condition_label = db.Column(db.String(100), nullable=True)  # e.g., 'Còn tốt', 'Cần kiểm tra'
    asset_type_id = db.Column(db.Integer, db.ForeignKey('asset_type.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # User who created/owns the asset
    user_text = db.Column(db.Text)  # User notes/description
    notes = db.Column(db.Text)  # Admin notes
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Assigned users (many-to-many)
    assigned_users = db.relationship(
        'User',
        secondary=asset_user,
        back_populates='assigned_assets',
        lazy='subquery'
    )
    
    def soft_delete(self):
        """Soft delete asset"""
        self.deleted_at = datetime.utcnow()
        self.status = 'disposed'
    
    def restore(self):
        """Restore deleted asset"""
        self.deleted_at = None
        if self.status == 'disposed':
            self.status = 'active'
    
    def __repr__(self):
        return f'<Asset {self.name}>'

# Audit log model
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    module = db.Column(db.String(50), nullable=False)  # assets, asset_types, users
    action = db.Column(db.String(20), nullable=False)   # create, update, delete
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))

    def __repr__(self):
        return f'<AuditLog {self.module}:{self.action}#{self.entity_id}>'

# IT Maintenance record
class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    maintenance_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    type = db.Column(db.String(50), nullable=False)  # maintenance, repair, inspection
    description = db.Column(db.Text)
    vendor = db.Column(db.String(200))
    person_in_charge = db.Column(db.String(120))
    cost = db.Column(db.Float, default=0.0)
    next_due_date = db.Column(db.Date)
    status = db.Column(db.String(30), default='completed')  # completed, scheduled
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset = db.relationship('Asset', backref=db.backref('maintenance_records', lazy=True))
    
    def soft_delete(self):
        """Soft delete maintenance record"""
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restore deleted maintenance record"""
        self.deleted_at = None

    def __repr__(self):
        return f'<Maintenance #{self.id} asset={self.asset_id}>'
