# Hướng dẫn chạy Docker với Nginx

## Cấu trúc

- **Nginx**: Reverse proxy, serve static files, expose port 80
- **Flask App**: Chạy trên port 5000 (internal)
- **PostgreSQL**: Database service

## Cách chạy

### 1. Build và chạy tất cả services

```bash
docker-compose up --build
```

### 2. Chạy ở background (detached mode)

```bash
docker-compose up -d --build
```

### 3. Xem logs

```bash
# Tất cả services
docker-compose logs -f

# Chỉ Nginx
docker-compose logs -f nginx

# Chỉ Flask app
docker-compose logs -f web

# Chỉ database
docker-compose logs -f db
```

### 4. Dừng services

```bash
docker-compose down
```

### 5. Dừng và xóa volumes (xóa database)

```bash
docker-compose down -v
```

## Truy cập ứng dụng

- **URL**: http://localhost (port 80)
- **Tài khoản mặc định**:
  - Username: `admin`
  - Password: `admin123`

## Cấu hình

### Thay đổi biến môi trường

Sửa file `docker-compose.yml` trong phần `environment` của service `web`:

```yaml
environment:
  - DATABASE_URL=postgresql://qlts_user:qlts_password@db:5432/qlts_db
  - SECRET_KEY=your-secret-key-change-in-production
  - ADMIN_USERNAME=admin
  - ADMIN_PASSWORD=admin123
```

### Thay đổi port Nginx

Sửa trong `docker-compose.yml`:

```yaml
nginx:
  ports:
    - "8080:80"  # Thay đổi 8080 thành port bạn muốn
```

### Cấu hình Nginx

Sửa file `nginx/nginx.conf` để thay đổi cấu hình Nginx.

## Kiểm tra services

```bash
# Xem trạng thái
docker-compose ps

# Kiểm tra health
curl http://localhost/healthz
```

## Troubleshooting

### Lỗi kết nối database

Đảm bảo service `db` đã start xong trước khi `web` start:
```bash
docker-compose up db
# Đợi vài giây
docker-compose up web nginx
```

### Lỗi permission

Nếu có lỗi permission với volumes:
```bash
sudo chown -R $USER:$USER instance/
```

### Rebuild lại từ đầu

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

