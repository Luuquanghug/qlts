#!/usr/bin/env python3
"""
Test cases cho ứng dụng quản lý tài sản
"""

import unittest
import os
import sys

# Thêm thư mục gốc vào Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Category, Employee, Asset

class TestAssetManagement(unittest.TestCase):
    """Test cases cho hệ thống quản lý tài sản"""
    
    def setUp(self):
        """Thiết lập test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Dọn dẹp sau mỗi test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_homepage(self):
        """Test trang chủ"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Dashboard', response.get_data(as_text=True))
    
    def test_assets_page(self):
        """Test trang danh sách tài sản"""
        response = self.app.get('/assets')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Tài sản', response.get_data(as_text=True))
    
    def test_categories_page(self):
        """Test trang danh sách danh mục"""
        response = self.app.get('/categories')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Danh mục', response.get_data(as_text=True))
    
    def test_employees_page(self):
        """Test trang danh sách nhân viên"""
        response = self.app.get('/employees')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Nhân viên', response.get_data(as_text=True))
    
    def test_add_category(self):
        """Test thêm danh mục"""
        with app.app_context():
            category = Category(name="Test Category", description="Test Description")
            db.session.add(category)
            db.session.commit()
            
            saved_category = Category.query.filter_by(name="Test Category").first()
            self.assertIsNotNone(saved_category)
            self.assertEqual(saved_category.name, "Test Category")
    
    def test_add_employee(self):
        """Test thêm nhân viên"""
        with app.app_context():
            employee = Employee(
                name="Test Employee",
                email="test@example.com",
                department="IT",
                position="Developer"
            )
            db.session.add(employee)
            db.session.commit()
            
            saved_employee = Employee.query.filter_by(email="test@example.com").first()
            self.assertIsNotNone(saved_employee)
            self.assertEqual(saved_employee.name, "Test Employee")
    
    def test_add_asset(self):
        """Test thêm tài sản"""
        with app.app_context():
            # Tạo danh mục và nhân viên trước
            category = Category(name="Test Category", description="Test Description")
            employee = Employee(name="Test Employee", email="test@example.com", department="IT", position="Developer")
            
            db.session.add(category)
            db.session.add(employee)
            db.session.commit()
            
            # Tạo tài sản
            from datetime import date
            asset = Asset(
                name="Test Asset",
                description="Test Asset Description",
                category_id=category.id,
                employee_id=employee.id,
                purchase_date=date.today(),
                purchase_price=1000000,
                status="active"
            )
            
            db.session.add(asset)
            db.session.commit()
            
            saved_asset = Asset.query.filter_by(name="Test Asset").first()
            self.assertIsNotNone(saved_asset)
            self.assertEqual(saved_asset.name, "Test Asset")
            self.assertEqual(saved_asset.purchase_price, 1000000)

if __name__ == '__main__':
    unittest.main()
