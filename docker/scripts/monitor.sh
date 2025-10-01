#!/bin/bash
# monitor.sh - 서비스 모니터링 및 관리 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 함수 정의
print_header() {
    echo -e "${CYAN}=========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}=========================================${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 실시간 모니터링
real_time_monitor() {
    while true; do
        clear
        print_header "🔍 News Platform Real-time Monitor"
        echo "$(date)"
        echo ""
        
        # 컨테이너 상태
        echo -e "${BLUE}📦 Container Status:${NC}"
        docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        # 리소스 사용량
        echo -e "${PURPLE}💻 Resource Usage:${NC}"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        echo ""
        
        # 로그 요약 (최근 5줄)
        echo -e "${YELLOW}📋 Recent Logs:${NC}"
        docker-compose logs --tail=3 backend | tail -3
        docker-compose logs --tail=3 consumer | tail -3
        echo ""
        
        # 헬스체크
        echo -e "${GREEN}❤️  Health Status:${NC}"
        check_service_health
        
        echo ""
        echo "Press Ctrl+C to exit..."
        sleep 5
    done
}

# 서비스 헬스체크
check_service_health() {
    local services=("postgres:5432" "kafka:9092" "elasticsearch:9200" "backend:8000" "frontend:80")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        
        if docker-compose exec -T "$name" sh -c "nc -z localhost $port" >/dev/null 2>&1; then
            echo -e "  ✅ $name ($port)"
        else
            echo -e "  ❌ $name ($port)"
        fi
    done
}

# 로그 분석
analyze_logs() {
    local service="$1"
    local lines="${2:-100}"
    
    if [ -z "$service" ]; then
        print_error "서비스명을 지정해주세요."
        echo "사용 가능한 서비스: backend, frontend, producer, consumer, postgres, kafka, elasticsearch"
        return 1
    fi
    
    print_header "📋 Log Analysis: $service (Last $lines lines)"
    
    # 에러 로그만 추출
    echo -e "${RED}🚨 Error Logs:${NC}"
    docker-compose logs --tail="$lines" "$service" | grep -i "error\|exception\|fail" || echo "No errors found"
    echo ""
    
    # 경고 로그
    echo -e "${YELLOW}⚠️  Warning Logs:${NC}"
    docker-compose logs --tail="$lines" "$service" | grep -i "warn" || echo "No warnings found"
    echo ""
    
    # 최근 로그
    echo -e "${BLUE}📝 Recent Logs:${NC}"
    docker-compose logs --tail=20 "$service"
}

# 성능 메트릭
performance_metrics() {
    print_header "📊 Performance Metrics"
    
    # CPU 및 메모리 사용량
    echo -e "${PURPLE}💻 Resource Usage:${NC}"
    docker stats --no-stream
    echo ""
    
    # 디스크 사용량
    echo -e "${BLUE}💾 Disk Usage:${NC}"
    docker system df
    echo ""
    
    # 네트워크 상태
    echo -e "${CYAN}🌐 Network Status:${NC}"
    docker network ls | grep news
    echo ""
    
    # 볼륨 사용량
    echo -e "${GREEN}📁 Volume Usage:${NC}"
    docker volume ls | grep news
}

# Kafka 상태 확인
kafka_status() {
    print_header "📡 Kafka Cluster Status"
    
    # 토픽 리스트
    echo -e "${BLUE}📋 Topics:${NC}"
    docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list || print_error "Failed to list topics"
    echo ""
    
    # 컨슈머 그룹 상태
    echo -e "${PURPLE}👥 Consumer Groups:${NC}"
    docker-compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list || print_error "Failed to list consumer groups"
    echo ""
    
    # 특정 토픽의 상세 정보
    echo -e "${GREEN}📊 Topic Details (news-raw):${NC}"
    docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic news-raw || print_error "Topic news-raw not found"
}

# Elasticsearch 상태 확인
elasticsearch_status() {
    print_header "🔍 Elasticsearch Status"
    
    # 클러스터 상태
    echo -e "${GREEN}🏥 Cluster Health:${NC}"
    curl -s "http://localhost:9200/_cluster/health?pretty" || print_error "Failed to get cluster health"
    echo ""
    
    # 인덱스 리스트
    echo -e "${BLUE}📋 Indices:${NC}"
    curl -s "http://localhost:9200/_cat/indices?v" || print_error "Failed to list indices"
    echo ""
    
    # 노드 정보
    echo -e "${PURPLE}🖥️  Nodes:${NC}"
    curl -s "http://localhost:9200/_cat/nodes?v" || print_error "Failed to get nodes info"
}

# 데이터베이스 상태 확인
database_status() {
    print_header "🗄️  Database Status"
    
    # 연결 상태
    echo -e "${GREEN}🔗 Connection Status:${NC}"
    docker-compose exec postgres pg_isready -h localhost -p 5432 || print_error "Database connection failed"
    echo ""
    
    # 데이터베이스 크기
    echo -e "${BLUE}📊 Database Size:${NC}"
    docker-compose exec postgres psql -U newsuser -d newsdb -c "SELECT pg_size_pretty(pg_database_size('newsdb')) as database_size;"
    echo ""
    
    # 테이블 목록
    echo -e "${PURPLE}📋 Tables:${NC}"
    docker-compose exec postgres psql -U newsuser -d newsdb -c "\\dt"
    echo ""
    
    # pgvector 확장 상태
    echo -e "${CYAN}🧩 Extensions:${NC}"
    docker-compose exec postgres psql -U newsuser -d newsdb -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
}

# 알림 설정
setup_alerts() {
    print_header "🔔 Alert Configuration"
    
    echo "This feature is under development..."
    echo "Future capabilities:"
    echo "- Email notifications for service failures"
    echo "- Slack integration"
    echo "- Custom threshold alerts"
    echo "- Log-based alerting"
}

# 백업 상태 확인
backup_status() {
    print_header "💾 Backup Status"
    
    if [ -d "backups" ]; then
        echo -e "${BLUE}📁 Available Backups:${NC}"
        ls -la backups/ | tail -10
        echo ""
        
        echo -e "${GREEN}📊 Backup Statistics:${NC}"
        echo "Total backups: $(ls backups/ | wc -l)"
        echo "Latest backup: $(ls -t backups/ | head -1)"
        echo "Oldest backup: $(ls -t backups/ | tail -1)"
    else
        print_warning "No backup directory found. Run deploy.sh backup to create your first backup."
    fi
}

# 사용법 출력
show_usage() {
    echo "사용법: $0 [명령어]"
    echo ""
    echo "명령어:"
    echo "  monitor                  실시간 모니터링"
    echo "  logs <서비스> [라인수]      로그 분석"
    echo "  performance             성능 메트릭 확인"
    echo "  kafka                   Kafka 상태 확인"
    echo "  elasticsearch           Elasticsearch 상태 확인"
    echo "  database                데이터베이스 상태 확인"
    echo "  backup-status           백업 상태 확인"
    echo "  alerts                  알림 설정"
    echo "  --help                  이 도움말 출력"
    echo ""
    echo "예시:"
    echo "  $0 monitor              # 실시간 모니터링 시작"
    echo "  $0 logs backend 50      # 백엔드 최근 50줄 로그 분석"
    echo "  $0 performance          # 성능 메트릭 확인"
}

# 메인 실행
main() {
    case "$1" in
        monitor)
            real_time_monitor
            ;;
        logs)
            analyze_logs "$2" "$3"
            ;;
        performance)
            performance_metrics
            ;;
        kafka)
            kafka_status
            ;;
        elasticsearch)
            elasticsearch_status
            ;;
        database)
            database_status
            ;;
        backup-status)
            backup_status
            ;;
        alerts)
            setup_alerts
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