pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'credit-score-api'
        DOCKER_TAG = 'latest'
        CONTAINER_PORT = '5000'
    }
    
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', 
                url: 'https://github.com/yenat/Interoperable-creditscore.git'
            }
        }
        
        stage('Build') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'DB_IP', variable: 'DB_IP'),
                        string(credentialsId: 'DB_PORT', variable: 'DB_PORT'), 
                        string(credentialsId: 'DB_SID', variable: 'DB_SID'),
                        string(credentialsId: 'DB_USERNAME', variable: 'DB_USERNAME'),
                        string(credentialsId: 'DB_PASSWORD', variable: 'DB_PASSWORD')
                    ]) {
                        sh """
                            docker build \
                                --build-arg DB_IP=${DB_IP} \
                                --build-arg DB_PORT=${DB_PORT} \
                                --build-arg DB_SID=${DB_SID} \
                                --build-arg DB_USERNAME=${DB_USERNAME} \
                                --build-arg DB_PASSWORD=${DB_PASSWORD} \
                                -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                        """
                    }
                }
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'DB_IP', variable: 'DB_IP'),
                        string(credentialsId: 'DB_PORT', variable: 'DB_PORT'),
                        string(credentialsId: 'DB_SID', variable: 'DB_SID'),
                        string(credentialsId: 'DB_USERNAME', variable: 'DB_USERNAME'),
                        string(credentialsId: 'DB_PASSWORD', variable: 'DB_PASSWORD')
                    ]) {
                        sh """
                            docker stop ${DOCKER_IMAGE} || true
                            docker rm ${DOCKER_IMAGE} || true
                            
                            docker run -d \
                                --name ${DOCKER_IMAGE} \
                                -p ${CONTAINER_PORT}:5000 \
                                -e DB_IP=${DB_IP} \
                                -e DB_PORT=${DB_PORT} \
                                -e DB_SID=${DB_SID} \
                                -e DB_USERNAME=${DB_USERNAME} \
                                -e DB_PASSWORD=${DB_PASSWORD} \
                                --restart unless-stopped \
                                ${DOCKER_IMAGE}:${DOCKER_TAG}
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo "Deployment completed for ${DOCKER_IMAGE}:${DOCKER_TAG}"
        }
    }
}