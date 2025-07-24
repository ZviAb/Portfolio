pipeline{
    agent any

    options {
        timeout(time: 10, unit: 'MINUTES')
        timestamps() 
    }

    environment {
        JWT_SECRET_KEY = credentials('jwt_secret_key')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Image') {
            steps {
                sh '''
                    docker compose --profile unit-test build unit-test
                '''
            }
        }

        stage('Unit Test') {
            steps {
                sh '''
                    docker compose --profile unit-test run --rm unit-test
                '''
            }
        }
    }

    post {
        success {
            echo '✅ Build and deploy completed successfully.'
        }
        failure {
            echo '❌ Build or deploy failed.'
        }
    }
}
