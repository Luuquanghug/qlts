FROM nginx:alpine

# Xóa cấu hình mặc định
RUN rm /etc/nginx/conf.d/default.conf

# Copy cấu hình Nginx
COPY nginx.conf /etc/nginx/conf.d/

# Expose port 80
EXPOSE 80

# Nginx tự động start khi container chạy
CMD ["nginx", "-g", "daemon off;"]

