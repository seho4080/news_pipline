#!/bin/bash
# deploy.sh - 서비스 배포 및 관리 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_deploy() {
    echo -e "${BLUE}[DEPLOY]${NC} $1"
}

print_service() {
    echo -e "${PURPLE}[SERVICE]${NC} $1"
}

# 환경 설정 확인
check_environment() {
    print_status "환경 설정을 확인합니다..."
    
    if [ ! -f .env ]; then
        print_error ".env 파일이 존재하지 않습니다. setup.sh를 먼저 실행해주세요."
        exit 1
    fi
    
    # 중요한 환경 변수들 확인
    source .env
    
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-openai-api-key" ]; then
        print_warning "⚠️  OPENAI_API_KEY가 설정되지 않았습니다."
    fi
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-super-secret-key-change-this-in-production" ]; then
        print_warning "⚠️  Django SECRET_KEY가 기본값입니다."
    fi
    
    print_status "✅ 환경 설정 확인 완료"
}

# 서비스 시작
start_services() {
    local env_mode="$1"
    
    print_deploy "서비스를 시작합니다..."
    
    if [ "$env_mode" = "production" ]; then
        print_deploy "🚀 프로덕션 모드로 배포합니다..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    else
        print_deploy "🔧 개발 모드로 배포합니다..."
        docker-compose up -d
    fi
    
    print_status "✅ 서비스가 시작되었습니다!"
}

# 서비스 상태 확인
check_services() {
    print_status "서비스 상태를 확인합니다..."
    echo ""
    
    # 컨테이너 상태 확인
    docker-compose ps
    echo ""
    
    # 헬스체크 확인
    print_status "헬스체크를 수행합니다..."
    
    sleep 10  # 서비스 시작 대기
    
    # PostgreSQL 확인
    if docker-compose exec -T postgres pg_isready -h localhost; then
        print_service "✅ PostgreSQL: 정상"
    else
        print_service "❌ PostgreSQL: 문제 발생"
    fi
    
    # Kafka 확인
    if docker-compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 >/dev/null 2>&1; then
        print_service "✅ Kafka: 정상"
    else
        print_service "❌ Kafka: 문제 발생"
    fi
    
    # Elasticsearch 확인
    if docker-compose exec -T elasticsearch curl -f http://localhost:9200/_cluster/health >/dev/null 2>&1; then
        print_service "✅ Elasticsearch: 정상"
    else
        print_service "❌ Elasticsearch: 문제 발생"
    fi
    
    # Backend 확인
    sleep 5
    if curl -f http://localhost:8000/health/ >/dev/null 2>&1; then
        print_service "✅ Backend: 정상"
    else
        print_service "❌ Backend: 문제 발생"
    fi
    
    # Frontend 확인
    if curl -f http://localhost/ >/dev/null 2>&1; then
        print_service "✅ Frontend: 정상"
    else
        print_service "❌ Frontend: 문제 발생"
    fi
}

# 로그 확인
show_logs() {
    local service="$1"
    
    if [ -z "$service" ]; then
        print_status "전체 서비스 로그를 출력합니다..."
        docker-compose logs -f
    else
        print_status "${service} 서비스 로그를 출력합니다..."
        docker-compose logs -f "$service"
    fi
}

# 서비스 중지
stop_services() {
    print_deploy "서비스를 중지합니다..."
    docker-compose down
    print_status "✅ 모든 서비스가 중지되었습니다."
}

# 완전 정리
cleanup() {
    print_warning "모든 컨테이너와 볼륨을 삭제합니다..."
    read -p "정말로 모든 데이터를 삭제하시겠습니까? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_status "✅ 정리가 완료되었습니다."
    else
        print_status "정리가 취소되었습니다."
    fi
}

# 데이터베이스 초기화
init_database() {
    print_deploy "데이터베이스를 초기화합니다..."
    
    # Django 마이그레이션 실행
    docker-compose exec backend python manage.py makemigrations
    docker-compose exec backend python manage.py migrate
    
    # 슈퍼유저 생성 (선택적)
    read -p "슈퍼유저를 생성하시겠습니까? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose exec backend python manage.py createsuperuser
    fi
    
    print_status "✅ 데이터베이스 초기화가 완료되었습니다."
}

# 백업
backup_data() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    print_status "데이터를 백업합니다: $backup_dir"
    
    # PostgreSQL 백업
    docker-compose exec -T postgres pg_dump -U newsuser newsdb > "$backup_dir/database.sql"
    
    # Elasticsearch 백업 (인덱스 정보만)
    curl -X GET "localhost:9200/_cat/indices?v" > "$backup_dir/elasticsearch_indices.txt"
    
    print_status "✅ 백업이 완료되었습니다: $backup_dir"
}

# 사용법 출력
show_usage() {
    echo "사용법: $0 [명령어] [옵션]"
    echo ""
    echo "명령어:"
    echo "  start [dev|production]   서비스 시작 (기본: dev)"
    echo "  stop                     서비스 중지"
    echo "  restart                  서비스 재시작"
    echo "  status                   서비스 상태 확인"
    echo "  logs [서비스명]           로그 확인"
    echo "  init-db                  데이터베이스 초기화"
    echo "  backup                   데이터 백업"
    echo "  cleanup                  완전 정리"
    echo "  --help                   이 도움말 출력"
    echo ""
    echo "예시:"
    echo "  $0 start                 # 개발 모드로 시작"
    echo "  $0 start production      # 프로덕션 모드로 시작"
    echo "  $0 logs backend          # 백엔드 로그만 확인"
}

# 메인 실행
main() {
    echo "========================================="
    echo "🚀 News Platform Deployment Manager"
    echo "========================================="
    
    case "$1" in
        start)
            check_environment
            start_services "$2"
            sleep 15
            check_services
            echo ""
            print_status "🎉 배포가 완료되었습니다!"
            echo ""
            echo "서비스 접속 정보:"
            echo "  Frontend: http://localhost"
            echo "  Backend API: http://localhost/api"
            echo "  Django Admin: http://localhost/admin"
            echo ""
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 5
            check_environment
            start_services "$2"
            ;;
        status)
            check_services
            ;;
        logs)
            show_logs "$2"
            ;;
        init-db)
            init_database
            ;;
        backup)
            backup_data
            ;;
        cleanup)
            cleanup
            ;;
        --help|help|"")
            show_usage
            ;;
        *)
            print_error "알 수 없는 명령어: $1"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"