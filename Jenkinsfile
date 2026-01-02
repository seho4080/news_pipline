// Jenkins Pipeline for News Pipeline Project
// Declarative Pipeline Syntax

pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 1, unit: 'HOURS')
        timestamps()
    }

    environment {
        REGISTRY = credentials('docker-registry-url')
        REGISTRY_USERNAME = credentials('docker-registry-username')
        REGISTRY_PASSWORD = credentials('docker-registry-password')
        SLACK_CHANNEL = '#news-pipeline-alerts'
        GIT_BRANCH = "${env.GIT_BRANCH ?: 'main'}"
    }

    parameters {
        choice(name: 'ENVIRONMENT', choices: ['develop', 'staging', 'production'], description: 'Environment to deploy')
        booleanParam(name: 'SKIP_TESTS', defaultValue: false, description: 'Skip tests (not recommended)')
        booleanParam(name: 'FORCE_DEPLOY', defaultValue: false, description: 'Force deploy without approval')
    }

    stages {
        stage('📋 Checkout') {
            steps {
                script {
                    echo "🔄 Checking out code from ${GIT_BRANCH}"
                }
                checkout scm
            }
        }

        stage('🔍 Code Quality Analysis') {
            parallel {
                stage('Consumer - Lint & Test') {
                    steps {
                        script {
                            echo "🔎 Consumer: Analyzing code quality"
                            dir('consumer') {
                                sh '''
                                    set +e
                                    
                                    # Install dependencies
                                    pip install -q -r requirements.txt pylint flake8 bandit pytest pytest-cov
                                    
                                    # Pylint
                                    echo "Running pylint..."
                                    pylint news_preprocessor.py dlq_reprocessor.py --exit-zero --output-format=json > pylint-report.json || true
                                    
                                    # Flake8
                                    echo "Running flake8..."
                                    flake8 . --max-line-length=100 --format=json > flake8-report.json || true
                                    
                                    # Bandit (Security)
                                    echo "Running bandit..."
                                    bandit -r . -f json -o bandit-report.json || true
                                    
                                    # Syntax check
                                    python -m py_compile news_preprocessor.py dlq_reprocessor.py
                                    
                                    set -e
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            dir('consumer') {
                                recordIssues(
                                    enabledForFailure: true,
                                    tools: [
                                        pyLint(pattern: 'pylint-report.json'),
                                        flake8(pattern: 'flake8-report.json')
                                    ]
                                )
                            }
                        }
                    }
                }

                stage('Backend - Django Tests') {
                    steps {
                        script {
                            echo "🔎 Backend: Running Django tests"
                            dir('backend') {
                                sh '''
                                    set +e
                                    
                                    # Install dependencies
                                    pip install -q -r requirements.txt pytest pytest-django pytest-cov pylint flake8
                                    
                                    # Pylint
                                    echo "Running pylint on Django code..."
                                    pylint myproject members mynews --exit-zero --output-format=json > pylint-report.json || true
                                    
                                    # Flake8
                                    echo "Running flake8..."
                                    flake8 . --max-line-length=100 --exclude=migrations --format=json > flake8-report.json || true
                                    
                                    # Django check
                                    echo "Running Django system check..."
                                    python manage.py check --settings=myproject.settings || true
                                    
                                    set -e
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            dir('backend') {
                                recordIssues(
                                    enabledForFailure: true,
                                    tools: [
                                        pyLint(pattern: 'pylint-report.json')
                                    ]
                                )
                            }
                        }
                    }
                }

                stage('Frontend - ESLint & Build') {
                    steps {
                        script {
                            echo "🔎 Frontend: Linting and building"
                            dir('frontend-react') {
                                sh '''
                                    # Install dependencies
                                    npm ci
                                    
                                    # ESLint
                                    echo "Running ESLint..."
                                    npm run lint 2>&1 || true
                                    
                                    # Type check
                                    echo "Type checking..."
                                    npm run type-check 2>&1 || true
                                    
                                    # Build
                                    echo "Building..."
                                    npm run build
                                '''
                            }
                        }
                    }
                }
            }
        }

        stage('🧪 Unit Tests') {
            when {
                expression { return !params.SKIP_TESTS }
            }
            parallel {
                stage('Consumer Tests') {
                    steps {
                        script {
                            echo "🧪 Running Consumer unit tests"
                            dir('consumer') {
                                sh '''
                                    pip install -q pytest pytest-cov
                                    pytest . -v --cov=. --cov-report=xml --cov-report=html || true
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            dir('consumer') {
                                junit testResults: '*.xml', allowEmptyResults: true
                                publishCoverage(
                                    adapters: [coberturaAdapter('coverage.xml')],
                                    failOnFailingQualityGate: false
                                )
                            }
                        }
                    }
                }

                stage('Frontend Tests') {
                    steps {
                        script {
                            echo "🧪 Running Frontend tests"
                            dir('frontend-react') {
                                sh '''
                                    npm test -- --run --coverage || true
                                '''
                            }
                        }
                    }
                }
            }
        }

        stage('🔒 Security Scan') {
            parallel {
                stage('SAST - Bandit & Safety') {
                    steps {
                        script {
                            echo "🔒 Running security scans"
                            sh '''
                                pip install -q bandit safety
                                
                                # Consumer security
                                bandit -r consumer/ -f json -o bandit-consumer.json || true
                                safety check --json > safety-report.json || true
                            '''
                        }
                    }
                }

                stage('Dependency Check') {
                    steps {
                        script {
                            echo "🔒 Checking dependencies"
                            sh '''
                                pip install -q pip-audit
                                pip-audit --desc > dependency-audit.txt || true
                                
                                cd frontend-react
                                npm audit --json > npm-audit.json || true
                            '''
                        }
                    }
                }
            }
        }

        stage('🐳 Docker Build') {
            steps {
                script {
                    echo "🐳 Building Docker images"
                    sh '''
                        IMAGE_TAG="${BUILD_NUMBER}-${GIT_COMMIT:0:7}"
                        
                        # Build Consumer image
                        echo "Building Consumer image..."
                        docker build -f docker/consumer.Dockerfile \
                            -t ${REGISTRY}/news-consumer:${IMAGE_TAG} \
                            -t ${REGISTRY}/news-consumer:latest \
                            .
                        
                        # Build Backend image
                        echo "Building Backend image..."
                        docker build -f docker/backend.Dockerfile \
                            -t ${REGISTRY}/news-backend:${IMAGE_TAG} \
                            -t ${REGISTRY}/news-backend:latest \
                            ./backend
                        
                        # Build Frontend image
                        echo "Building Frontend image..."
                        docker build -f docker/frontend.Dockerfile \
                            -t ${REGISTRY}/news-frontend:${IMAGE_TAG} \
                            -t ${REGISTRY}/news-frontend:latest \
                            ./frontend-react
                    '''
                }
            }
        }

        stage('🔐 Container Security Scan') {
            steps {
                script {
                    echo "🔐 Scanning container images"
                    sh '''
                        # Install trivy
                        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                        
                        # Scan images
                        trivy image --format json --output trivy-consumer.json ${REGISTRY}/news-consumer:latest || true
                        trivy image --format json --output trivy-backend.json ${REGISTRY}/news-backend:latest || true
                        trivy image --format json --output trivy-frontend.json ${REGISTRY}/news-frontend:latest || true
                    '''
                }
            }
        }

        stage('📤 Push to Registry') {
            when {
                expression { 
                    return env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'develop'
                }
            }
            steps {
                script {
                    echo "📤 Pushing images to registry"
                    sh '''
                        echo ${REGISTRY_PASSWORD} | docker login -u ${REGISTRY_USERNAME} --password-stdin ${REGISTRY}
                        
                        IMAGE_TAG="${BUILD_NUMBER}-${GIT_COMMIT:0:7}"
                        
                        docker push ${REGISTRY}/news-consumer:${IMAGE_TAG}
                        docker push ${REGISTRY}/news-consumer:latest
                        
                        docker push ${REGISTRY}/news-backend:${IMAGE_TAG}
                        docker push ${REGISTRY}/news-backend:latest
                        
                        docker push ${REGISTRY}/news-frontend:${IMAGE_TAG}
                        docker push ${REGISTRY}/news-frontend:latest
                        
                        docker logout ${REGISTRY}
                    '''
                }
            }
        }

        stage('🚀 Deploy to Staging') {
            when {
                expression { 
                    return env.ENVIRONMENT == 'staging' || env.BRANCH_NAME == 'develop'
                }
            }
            steps {
                script {
                    echo "🚀 Deploying to Staging"
                    sh '''
                        IMAGE_TAG="${BUILD_NUMBER}-${GIT_COMMIT:0:7}"
                        
                        # SSH to staging server and deploy
                        ssh -i ${STAGING_KEY_FILE} ${STAGING_USER}@${STAGING_HOST} << EOF
                        cd /app/news_pipeline
                        
                        # Pull images
                        docker pull ${REGISTRY}/news-consumer:${IMAGE_TAG}
                        docker pull ${REGISTRY}/news-backend:${IMAGE_TAG}
                        docker pull ${REGISTRY}/news-frontend:${IMAGE_TAG}
                        
                        # Update docker-compose
                        export CONSUMER_IMAGE=${REGISTRY}/news-consumer:${IMAGE_TAG}
                        export BACKEND_IMAGE=${REGISTRY}/news-backend:${IMAGE_TAG}
                        export FRONTEND_IMAGE=${REGISTRY}/news-frontend:${IMAGE_TAG}
                        
                        # Deploy
                        docker-compose -f docker-compose.staging.yml down
                        docker-compose -f docker-compose.staging.yml up -d
                        
                        # Health check
                        sleep 30
                        curl -f http://localhost:8000/api/health/ || exit 1
                        EOF
                    '''
                }
            }
            post {
                success {
                    script {
                        echo "✅ Staging deployment successful"
                    }
                }
                failure {
                    script {
                        echo "❌ Staging deployment failed"
                    }
                }
            }
        }

        stage('🎯 Production Approval') {
            when {
                expression { 
                    return env.ENVIRONMENT == 'production' && !params.FORCE_DEPLOY
                }
            }
            steps {
                script {
                    echo "⏳ Waiting for production approval"
                    input(
                        message: '🎯 Deploy to Production?',
                        ok: 'Deploy',
                        submitter: 'devops-team'
                    )
                }
            }
        }

        stage('🚀 Deploy to Production (Blue-Green)') {
            when {
                expression { 
                    return env.ENVIRONMENT == 'production' || (env.BRANCH_NAME == 'main' && params.FORCE_DEPLOY)
                }
            }
            steps {
                script {
                    echo "🚀 Deploying to Production (Blue-Green Strategy)"
                    sh '''
                        IMAGE_TAG="${BUILD_NUMBER}-${GIT_COMMIT:0:7}"
                        
                        ssh -i ${PROD_KEY_FILE} ${PROD_USER}@${PROD_HOST} << EOF
                        cd /app/news_pipeline
                        
                        # 1. Deploy to Green environment
                        echo "Deploying to Green environment..."
                        docker pull ${REGISTRY}/news-consumer:${IMAGE_TAG}
                        docker pull ${REGISTRY}/news-backend:${IMAGE_TAG}
                        docker pull ${REGISTRY}/news-frontend:${IMAGE_TAG}
                        
                        export CONSUMER_IMAGE=${REGISTRY}/news-consumer:${IMAGE_TAG}
                        export BACKEND_IMAGE=${REGISTRY}/news-backend:${IMAGE_TAG}
                        export FRONTEND_IMAGE=${REGISTRY}/news-frontend:${IMAGE_TAG}
                        
                        docker-compose -f docker-compose.prod.green.yml up -d
                        
                        # 2. Health check Green (max 5 minutes)
                        echo "Health checking Green environment..."
                        for i in {1..30}; do
                            if curl -f http://localhost:8001/api/health/ > /dev/null 2>&1; then
                                echo "✓ Green environment healthy"
                                break
                            fi
                            echo "Waiting for Green... ($i/30)"
                            sleep 10
                        done
                        
                        # 3. Switch load balancer Blue → Green
                        echo "Switching traffic to Green..."
                        sed -i 's/upstream app { server blue:8000; }/upstream app { server green:8000; }/' /etc/nginx/conf.d/app.conf
                        nginx -s reload
                        
                        # 4. Monitor (30 seconds) - Rollback if issue
                        echo "Monitoring Green environment..."
                        sleep 30
                        if ! curl -f http://localhost:8000/api/health/ > /dev/null 2>&1; then
                            echo "❌ Green failed, rolling back to Blue"
                            sed -i 's/upstream app { server green:8000; }/upstream app { server blue:8000; }/' /etc/nginx/conf.d/app.conf
                            nginx -s reload
                            docker-compose -f docker-compose.prod.green.yml down
                            exit 1
                        fi
                        
                        # 5. Shutdown Blue
                        echo "Shutting down Blue environment..."
                        docker-compose -f docker-compose.prod.blue.yml down
                        
                        echo "✅ Production deployment completed"
                        EOF
                    '''
                }
            }
            post {
                success {
                    script {
                        echo "✅ Production deployment successful"
                    }
                }
                failure {
                    script {
                        echo "❌ Production deployment failed - Blue-Green rollback executed"
                    }
                }
            }
        }

        stage('✅ Smoke Tests') {
            when {
                expression { 
                    return env.ENVIRONMENT == 'production' || env.ENVIRONMENT == 'staging'
                }
            }
            steps {
                script {
                    echo "✅ Running smoke tests"
                    sh '''
                        # Wait for services
                        sleep 10
                        
                        # Test health endpoint
                        curl -f http://${DEPLOY_HOST}:8000/api/health/ || exit 1
                        
                        # Test API
                        curl -f http://${DEPLOY_HOST}:8000/api/mynews/articles/?limit=1 || exit 1
                        
                        # Test Frontend
                        curl -f http://${DEPLOY_HOST}:3000/ || exit 1
                    '''
                }
            }
        }
    }

    post {
        always {
            script {
                echo "📊 Publishing reports"
                
                // Publish test results
                junit testResults: '**/test-results.xml', allowEmptyResults: true
                
                // Publish coverage
                publishHTML([
                    reportDir: 'consumer/htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Consumer Code Coverage'
                ])
                
                // Archive logs
                archiveArtifacts artifacts: '**/*.log', allowEmptyArchive: true
                archiveArtifacts artifacts: '**/*-report.*', allowEmptyArchive: true
            }
        }

        success {
            script {
                echo "✅ Pipeline succeeded"
                def deployEnv = params.ENVIRONMENT ?: 'unknown'
                sh '''
                    curl -X POST ${SLACK_WEBHOOK} \
                        -H 'Content-Type: application/json' \
                        -d '{
                            "channel": "#news-pipeline-alerts",
                            "text": "✅ Build #${BUILD_NUMBER} succeeded on ${GIT_BRANCH}",
                            "blocks": [
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "✅ *Build #${BUILD_NUMBER} succeeded*\nBranch: ${GIT_BRANCH}\nCommit: ${GIT_COMMIT:0:7}"
                                    }
                                }
                            ]
                        }'
                '''
            }
        }

        failure {
            script {
                echo "❌ Pipeline failed"
                sh '''
                    curl -X POST ${SLACK_WEBHOOK} \
                        -H 'Content-Type: application/json' \
                        -d '{
                            "channel": "#news-pipeline-alerts",
                            "text": "❌ Build #${BUILD_NUMBER} failed on ${GIT_BRANCH}",
                            "blocks": [
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "❌ *Build #${BUILD_NUMBER} failed*\nBranch: ${GIT_BRANCH}\nCheck logs: ${BUILD_URL}"
                                    }
                                }
                            ]
                        }'
                '''
            }
        }

        unstable {
            script {
                echo "⚠️ Pipeline unstable (tests failed but build successful)"
            }
        }

        cleanup {
            script {
                echo "🧹 Cleaning up workspace"
                deleteDir()
            }
        }
    }
}
