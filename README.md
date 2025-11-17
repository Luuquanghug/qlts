# Hệ thống Quản lý Tài sản Công ty

Ứng dụng web quản lý tài sản công ty được xây dựng bằng Python Flask với giao diện AdminLTE.

## Tính năng

- **Dashboard**: Tổng quan thống kê tài sản, danh mục, nhân viên
- **Quản lý tài sản**: Thêm, sửa, xóa, xem danh sách tài sản
- **Quản lý danh mục**: Phân loại tài sản theo danh mục
- **Quản lý nhân viên**: Quản lý thông tin nhân viên sử dụng tài sản
- **Giao diện responsive**: Sử dụng AdminLTE với sidebar navigation

## Công nghệ sử dụng

- **Backend**: Python Flask
- **Database**: SQLite (có thể chuyển sang PostgreSQL/MySQL)
- **Frontend**: HTML, CSS, JavaScript, AdminLTE
- **ORM**: SQLAlchemy
- **Migration**: Flask-Migrate

## Cài đặt

1. **Clone repository**:

```bash
git clone <repository-url>
cd QLTaiSan
```

2. **Tạo virtual environment**:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Cài đặt dependencies**:

```bash
pip install -r requirements.txt
```

4. **Cấu hình database**:
   Tạo file `.env` trong thư mục gốc:

```env
DATABASE_URL=sqlite:///asset_management.db
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True
```

5. **Khởi tạo database**:

```bash
python app.py
```

6. **Chạy ứng dụng**:

```bash
python app.py
```

Truy cập ứng dụng tại: http://localhost:5000

## Cấu trúc thư mục

```
QLTaiSan/
├── app.py                 # File chính của ứng dụng
├── models.py              # Định nghĩa models database
├── config.py              # Cấu hình ứng dụng
├── requirements.txt       # Dependencies Python
├── README.md             # Tài liệu hướng dẫn
├── static/               # File tĩnh (CSS, JS, images)
│   ├── css/
│   │   └── custom.css
│   └── js/
│       └── custom.js
├── templates/            # Templates HTML
│   ├── layouts/
│   │   └── base.html
│   ├── assets/
│   │   ├── list.html
│   │   ├── add.html
│   │   └── edit.html
│   ├── categories/
│   │   ├── list.html
│   │   └── add.html
│   ├── employees/
│   │   ├── list.html
│   │   └── add.html
│   └── index.html
└── test/                 # Thư mục test
```

## Sử dụng

### 1. Thêm danh mục tài sản

- Truy cập "Danh mục" từ sidebar
- Click "Thêm danh mục"
- Nhập tên và mô tả danh mục

### 2. Thêm nhân viên

- Truy cập "Nhân viên" từ sidebar
- Click "Thêm nhân viên"
- Nhập thông tin nhân viên

### 3. Thêm tài sản

- Truy cập "Tài sản" từ sidebar
- Click "Thêm tài sản"
- Chọn danh mục và nhân viên sử dụng
- Nhập thông tin tài sản

### 4. Quản lý tài sản

- Xem danh sách tài sản
- Chỉnh sửa thông tin tài sản
- Xóa tài sản
- Cập nhật trạng thái tài sản

## Cấu hình Database

Ứng dụng sử dụng SQLite mặc định. Để chuyển sang PostgreSQL hoặc MySQL:

1. Cài đặt driver database:

```bash
# PostgreSQL
pip install psycopg2-binary

# MySQL
pip install PyMySQL
```

2. Cập nhật `DATABASE_URL` trong file `.env`:

```env
# PostgreSQL
DATABASE_URL=postgresql://username:password@localhost/asset_management

# MySQL
DATABASE_URL=mysql+pymysql://username:password@localhost/asset_management
```

## Phát triển

### Thêm tính năng mới

1. Tạo model trong `models.py`
2. Thêm routes trong `app.py`
3. Tạo templates trong thư mục `templates/`
4. Cập nhật navigation trong `base.html`

### Chạy test

```bash
python -m pytest test/
```

## License

MIT License
