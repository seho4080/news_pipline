# Frontend Dockerfile for React App
FROM node:18-alpine as builder

WORKDIR /app

# 패키지 파일 복사 및 의존성 설치
COPY frontend/package*.json ./
RUN npm ci --only=production

# 소스 코드 복사
COPY frontend/ .

# 빌드 실행
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine

# 커스텀 Nginx 설정 복사
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf

# 빌드된 정적 파일 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# 포트 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]