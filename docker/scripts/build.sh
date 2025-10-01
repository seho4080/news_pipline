#!/bin/bash
# build.sh - Docker 이미지 빌드 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_build() {
    echo -e "${BLUE}[BUILD]${NC} $1"
}

# 빌드 시작 시간
START_TIME=$(date +%s)

# Docker 이미지 빌드
build_images() {
    print_status "Docker 이미지 빌드를 시작합니다..."
    
    # Frontend 빌드
    print_build "🌐 Frontend (React + Nginx) 이미지를 빌드합니다..."
    docker build -f docker/frontend.Dockerfile -t news-frontend:latest .
    
    # Backend 빌드
    print_build "🖥️  Backend (Django) 이미지를 빌드합니다..."
    docker build -f docker/backend.Dockerfile -t news-backend:latest .
    
    # Producer 빌드
    print_build "📡 Producer (Kafka Producer) 이미지를 빌드합니다..."
    docker build -f docker/producer.Dockerfile -t news-producer:latest .
    
    # Consumer 빌드
    print_build "⚙️  Consumer (News Preprocessor) 이미지를 빌드합니다..."
    docker build -f docker/consumer.Dockerfile -t news-consumer:latest .
    
    print_status "✅ 모든 이미지 빌드가 완료되었습니다!"
}

# 이미지 크기 확인
check_image_sizes() {
    print_status "빌드된 이미지 크기를 확인합니다..."
    echo ""
    docker images | grep "news-" | awk '{printf "%-20s %-15s %-15s\n", $1, $2, $7}'
    echo ""
}

# 빌드 캐시 정리 옵션
clean_build_cache() {
    if [ "$1" = "--clean" ]; then
        print_warning "빌드 캐시를 정리합니다..."
        docker builder prune -f
        print_status "✅ 빌드 캐시가 정리되었습니다."
    fi
}

# 개발용 빌드 (캐시 없음)
dev_build() {
    if [ "$1" = "--dev" ]; then
        print_warning "개발 모드로 빌드합니다 (캐시 없음)..."
        
        docker build --no-cache -f docker/frontend.Dockerfile -t news-frontend:dev .
        docker build --no-cache -f docker/backend.Dockerfile -t news-backend:dev .
        docker build --no-cache -f docker/producer.Dockerfile -t news-producer:dev .
        docker build --no-cache -f docker/consumer.Dockerfile -t news-consumer:dev .
        
        print_status "✅ 개발용 이미지 빌드가 완료되었습니다!"
        return 0
    fi
}

# 특정 서비스만 빌드
build_specific_service() {
    case "$1" in
        frontend)
            print_build "🌐 Frontend만 빌드합니다..."
            docker build -f docker/frontend.Dockerfile -t news-frontend:latest .
            ;;
        backend)
            print_build "🖥️  Backend만 빌드합니다..."
            docker build -f docker/backend.Dockerfile -t news-backend:latest .
            ;;
        producer)
            print_build "📡 Producer만 빌드합니다..."
            docker build -f docker/producer.Dockerfile -t news-producer:latest .
            ;;
        consumer)
            print_build "⚙️  Consumer만 빌드합니다..."
            docker build -f docker/consumer.Dockerfile -t news-consumer:latest .
            ;;
        *)
            return 1
            ;;
    esac
    print_status "✅ $1 이미지 빌드가 완료되었습니다!"
    return 0
}

# 사용법 출력
show_usage() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  --clean              빌드 캐시 정리 후 빌드"
    echo "  --dev                개발 모드 빌드 (캐시 없음)"
    echo "  frontend             Frontend만 빌드"
    echo "  backend              Backend만 빌드"
    echo "  producer             Producer만 빌드"
    echo "  consumer             Consumer만 빌드"
    echo "  --help               이 도움말 출력"
}

# 메인 실행
main() {
    echo "========================================="
    echo "🏗️  News Platform Docker Build"
    echo "========================================="
    
    # 매개변수 확인
    if [ "$1" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    # 개발 빌드 확인
    if dev_build "$1"; then
        return 0
    fi
    
    # 특정 서비스 빌드 확인
    if build_specific_service "$1"; then
        check_image_sizes
        return 0
    fi
    
    # 기본 빌드
    clean_build_cache "$1"
    build_images
    check_image_sizes
    
    # 빌드 시간 계산
    END_TIME=$(date +%s)
    BUILD_TIME=$((END_TIME - START_TIME))
    
    echo "========================================="
    print_status "🎉 빌드 완료! (소요 시간: ${BUILD_TIME}초)"
    echo "========================================="
    echo ""
    echo "다음 단계:"
    echo "  ./docker/scripts/deploy.sh - 서비스 배포"
    echo "  docker-compose up -d - 직접 서비스 시작"
}

main "$@"