pipeline {
    agent any

    environment {
        DOCKER_HUB_USER = 'aaditya0421'
        APP_NAME = 'agri-triage'
        IMAGE_NAME = "${DOCKER_HUB_USER}/${APP_NAME}"
        DOCKER_HUB_CREDENTIALS_ID = 'docker-hub-credentials'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:latest ."
                sh "docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:${BUILD_NUMBER}"
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: DOCKER_HUB_CREDENTIALS_ID, usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        sh "echo $PASS | docker login -u $USER --password-stdin"
                        sh "docker push ${IMAGE_NAME}:latest"
                        sh "docker push ${IMAGE_NAME}:${BUILD_NUMBER}"
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh "kubectl apply -f k8s/secret.yaml"
                sh "kubectl apply -f k8s/service.yaml"
                sh "kubectl apply -f k8s/deployment.yaml"
                sh "kubectl rollout restart deployment/agri-triage-deployment"
            }
        }
    }

    post {
        always {
            sh "docker logout"
        }
    }
}
