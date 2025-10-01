#!/bin/bash
# setup.sh - 프로젝트 초기 설정 스크립트

set -e

echo "🚀 News Platform Docker 환경 설정을 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 필요한 도구들 확인
check_requirements() {
    print_status "시스템 요구사항을 확인합니다..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker가 설치되어 있지 않습니다."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose가 설치되어 있지 않습니다."
        exit 1
    fi
    
    # Docker 서비스 실행 확인
    if ! docker info &> /dev/null; then
        print_error "Docker 서비스가 실행되지 않습니다."
        exit 1
    fi
    
    print_status "✅ 시스템 요구사항이 충족되었습니다."
}

# 환경 변수 파일 설정
setup_env_file() {
    print_status "환경 변수 파일을 설정합니다..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_status "✅ .env.example을 복사하여 .env 파일을 생성했습니다."
            print_warning "⚠️  .env 파일을 편집하여 실제 값으로 수정해주세요!"
        else
            print_error ".env.example 파일을 찾을 수 없습니다."
            exit 1
        fi
    else
        print_status "✅ .env 파일이 이미 존재합니다."
    fi
}

# 디렉토리 구조 생성
create_directories() {
    print_status "필요한 디렉토리를 생성합니다..."
    
    mkdir -p logs
    mkdir -p docker/ssl
    mkdir -p data/postgres
    mkdir -p data/elasticsearch
    mkdir -p data/kafka
    
    print_status "✅ 디렉토리 구조가 생성되었습니다."
}

# Docker 네트워크 생성
setup_docker_network() {
    print_status "Docker 네트워크를 설정합니다..."
    
    if ! docker network ls | grep -q "news-network"; then
        docker network create news-network
        print_status "✅ news-network 네트워크를 생성했습니다."
    else
        print_status "✅ news-network 네트워크가 이미 존재합니다."
    fi
}

# 권한 설정
set_permissions() {
    print_status "파일 권한을 설정합니다..."
    
    chmod +x docker/scripts/*.sh
    chmod +x docker/init-scripts/*.sh
    
    print_status "✅ 실행 권한이 설정되었습니다."
}

# 메인 실행
main() {
    echo "========================================="
    echo "🏗️  News Platform Docker Setup"
    echo "========================================="
    
    check_requirements
    setup_env_file
    create_directories
    setup_docker_network
    set_permissions
    
    echo ""
    echo "========================================="
    print_status "🎉 설정이 완료되었습니다!"
    echo "========================================="
    echo ""
    echo "다음 단계:"
    echo "1. .env 파일을 편집하여 실제 값으로 수정"
    echo "2. ./docker/scripts/build.sh 실행하여 이미지 빌드"
    echo "3. ./docker/scripts/deploy.sh 실행하여 서비스 시작"
    echo ""
    print_warning "주의: OpenAI API 키 등 중요한 설정을 반드시 확인하세요!"
}

main "$@"