pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'credit-score-api'
        DOCKER_TAG = 'latest'
    }
    
    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/yenat/Interoperable-creditscore.git', 
                     branch: 'main'
            }
        }
        
        stage('Build') {
            steps {
                script {
                    // Create temporary .env file
                    withCredentials([
                        string(credentialsId: 'DB_IP', variable: 'DB_IP'),
                        string(credentialsId: 'DB_PORT', variable: 'DB_PORT'),
                        string(credentialsId: 'DB_SID', variable: 'DB_SID'),
                        string(credentialsId: 'DB_USERNAME', variable: 'DB_USERNAME'),
                        string(credentialsId: 'DB_PASSWORD', variable: 'DB_PASSWORD')
                    ]) {
                        sh """
                            echo "DB_IP=${DB_IP}" > .env
                            echo "DB_PORT=${DB_PORT}" >> .env
                            echo "DB_SID=${DB_SID}" >> .env
                            echo "DB_USERNAME=${DB_USERNAME}" >> .env
                            echo "DB_PASSWORD=${DB_PASSWORD}" >> .env
                        """
                        
                        docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                    }
                }
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'DB_IP', variable: 'DB_IP'),
                        // Repeat for other credentials...
                    ]) {
                        sh """
                            docker run -d \
                                --name ${DOCKER_IMAGE} \
                                -p 5000:5000 \
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
}