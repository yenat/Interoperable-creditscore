pipeline {
    agent any
    
    environment {
        // Docker image settings
        DOCKER_IMAGE = 'interoperable-credit-score-api'
        DOCKER_TAG = 'latest'
        API_PORT = '5000'  // Your app's port (from app.py)
        
        // Database credentials (from Jenkins credentials store)
        DB_IP = credentials('DB_IP')
        DB_PORT = credentials('DB_PORT')
        DB_SID = credentials('DB_SID')
        DB_USERNAME = credentials('DB_USERNAME')
        DB_PASSWORD = credentials('DB_PASSWORD')
    }
    
    stages {
        stage('Build Docker Image') {
            steps {
                script {
                    // Build with database credentials as build args
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}", 
                        "--build-arg DB_IP=${DB_IP} " +
                        "--build-arg DB_PORT=${DB_PORT} " +
                        "--build-arg DB_SID=${DB_SID} " +
                        "--build-arg DB_USERNAME=${DB_USERNAME} " +
                        "--build-arg DB_PASSWORD=${DB_PASSWORD} ."
                    )
                }
            }
        }
        
        stage('Deploy API') {
            steps {
                script {
                    // Stop and remove old container (if exists)
                    sh "docker stop ${DOCKER_IMAGE} || true"
                    sh "docker rm ${DOCKER_IMAGE} || true"
                    
                    // Deploy new container with DB env vars
                    sh """
                        docker stop interoperable-credit-score-api || true
                        docker rm interoperable-credit-score-api || true
                        
                        docker run -d \
                            --network host \  
                            --name interoperable-credit-score-api \
                            -p 5000:5000 \
                            -e DB_IP=${DB_IP} \
                            -e DB_PORT=${DB_PORT} \
                            -e DB_SID=${DB_SID} \
                            -e DB_USERNAME=${DB_USERNAME} \
                            -e DB_PASSWORD=${DB_PASSWORD} \
                            --restart unless-stopped \
                            interoperable-credit-score-api:latest
                    """
                    
                    // Basic health check (ensure container stays running)
                    sleep(time: 5, unit: 'SECONDS')
                    def isRunning = sh(
                        returnStdout: true,
                        script: "docker inspect -f '{{.State.Running}}' ${DOCKER_IMAGE} || echo 'false'"
                    ).trim()
                    
                    if (isRunning != "true") {
                        error("Container failed to start!")
                    }
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Log container status (debugging)
                sh """
                    echo "### Container Status ###"
                    docker ps -a --filter "name=${DOCKER_IMAGE}"
                    echo "\\n### Recent Logs ###"
                    docker logs ${DOCKER_IMAGE} --tail 50 || true
                """
            }
        }
    }
}