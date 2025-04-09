pipeline {
    agent any
    
    environment {
        DB_IP = credentials('db_ip')
        DB_PORT = credentials('db_port')
        DB_SID = credentials('db_sid')
        DB_USERNAME = credentials('db_username')
        DB_PASSWORD = credentials('db_password')
    }
    
    stages {
        stage('Build') {
            steps {
                script {
                    // Build Docker image
                    docker.build("credit-score-api:${env.BUILD_ID}")
                }
            }
        }
        
        stage('Test') {
            steps {
                script {
                    // Run tests (you should add proper tests)
                    def testContainer = docker.image("credit-score-api:${env.BUILD_ID}").run("-e DB_IP=${DB_IP} -e DB_PORT=${DB_PORT} -e DB_SID=${DB_SID} -e DB_USERNAME=${DB_USERNAME} -e DB_PASSWORD=${DB_PASSWORD} -p 5000:5000")
                    
                    // Simple API test
                    def response = sh(script: "curl -X POST http://localhost:5000/predict -H 'Content-Type: application/json' -d '{\"fayda_number\":\"test\",\"type\":\"CREDIT_SCORE\",\"data\":[{\"card_number\":\"123\"}]}'", returnStdout: true)
                    
                    // Verify response format
                    if (!response.contains('score') || !response.contains('risk_level')) {
                        error("API test failed: Invalid response format")
                    }
                    
                    testContainer.stop()
                }
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Push to container registry (example for AWS ECR)
                    docker.withRegistry('https://your-registry-url', 'ecr-credentials') {
                        docker.image("credit-score-api:${env.BUILD_ID}").push()
                    }
                    
                    // Deploy to production (example for ECS)
                    sh "aws ecs update-service --cluster your-cluster --service your-service --force-new-deployment"
                }
            }
        }
    }
    
    post {
        always {
            // Clean up
            sh "docker rmi credit-score-api:${env.BUILD_ID} || true"
        }
    }
}