pipeline{
    agent any

    options {
        timeout(time: 10, unit: 'MINUTES')
        timestamps() 
    }

    environment {
        JWT_SECRET_KEY = credentials('jwt_secret_key')
        DB_NAME = credentials('Portfolio_DB_NAME')
        DB_USER = credentials('Portfolio_DB_USER')
        DB_PASSWORD = credentials('Portfolio_DB_PASSWORD')
        DATABASE_URL = credentials('Portfolio_DATABASE_URL')
        AWS_ECR_URL = credentials('ecr')
        AWS_DEFAULT_REGION = "ap-south-1"
        NOTIFICATION_EMAIL = "zviabra10@gmail.com"
    }

    stages {
        stage('Checkout') {
            steps {
                script { 
                    env.CURRENT_STAGE = 'Checkout'
                    echo "Current stage: ${env.CURRENT_STAGE}"
                }
                checkout scm
            }
        }
        
        // It's the same Dockerfile but with the part of the tests
        
        stage('Build Image for tests') {
            steps {
                script { 
                    env.CURRENT_STAGE = 'Build Image for tests'
                    echo "Current stage: ${env.CURRENT_STAGE}"
                }
                sh '''docker compose --profile unit-test build unit-test'''
            }
        }

        stage('Unit Test') {
            steps {
                script { 
                    env.CURRENT_STAGE = 'Unit Test'
                    echo "Current stage: ${env.CURRENT_STAGE}"
                }
                sh '''docker compose --profile unit-test run --rm unit-test'''
            }
        }

        stage('Package') {
            steps {
                script { 
                    env.CURRENT_STAGE = 'Package'
                    echo "Current stage: ${env.CURRENT_STAGE}"
                }
                sh '''docker compose --profile app build'''
            }
        }

        stage('E2E Tests') {
            when {
                expression { env.BRANCH_NAME?.startsWith('feature/') || env.BRANCH_NAME == 'main' }
            }
            steps {
                script { 
                    env.CURRENT_STAGE = 'E2E Tests'
                    echo "Current stage: ${env.CURRENT_STAGE}"
                }
                sh ''' 
                    docker compose --profile app up -d
                    docker compose --profile e2e run --rm e2e
                    docker compose --profile app down
                '''
            }
        }

        stage('Tag') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                script { 
                    env.CURRENT_STAGE = 'Tag'
                    echo "Current stage: ${env.CURRENT_STAGE}"
                    versionCalculation()
                    sshagent(credentials: ['gitlabssh']) {
                        sh '''
                            docker tag portfolio-application_main-app:latest ${AWS_ECR_URL}:${CALCULATED_VERSION}
                            git config user.name "jenkins"
                            git config user.email "jenkins@example.com"
                            git tag -a "${CALCULATED_VERSION}" -m "${CALCULATED_VERSION}"
                            git push origin "${CALCULATED_VERSION}"
                        '''
                    }
                }
            }
        }

        stage('Publish') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                script { 
                    env.CURRENT_STAGE = 'Publish'
                    echo "Current stage: ${env.CURRENT_STAGE}"
                }
                sh '''
                    aws ecr get-login-password --region ${AWS_DEFAULT_REGION} \
                      | docker login --username AWS --password-stdin ${AWS_ECR_URL}

                    docker push ${AWS_ECR_URL}:${CALCULATED_VERSION}
                '''
            }
        } 

        stage('Deploy') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                script { 
                    env.CURRENT_STAGE = 'Deploy'
                    echo "Current stage: ${env.CURRENT_STAGE}"
                }
                sshagent(credentials: ['gitlabssh']) {
                    sh """
                        echo 'Cloning helm charts repo...'
                        git clone git@gitlab.com:zviabramovich22-group/portfolio-gitops.git

                        echo 'Updating image tag in values.yaml...'
                        sed -i '/app:/,/^[^ ]/ { /image:/,/tag:/ s/\\(tag:[[:space:]]*\\).*/\\1${CALCULATED_VERSION}/ }' ./portfolio-gitops/application/values.yaml

                        echo 'Updating appVersion in Chart.yaml...'
                        sed -i 's/^\\(appVersion:[[:space:]]*\\).*/\\1${CALCULATED_VERSION}/' ./portfolio-gitops/application/Chart.yaml

                        cd portfolio-gitops
                        git config user.email "jenkins@example.com"
                        git config user.name "Jenkins CI"
                        git add application/values.yaml application/Chart.yaml
                        git commit -m "Updating version: ${CALCULATED_VERSION}"
                        git push origin HEAD:main
                    """
                }
            }
        } 
    }

    post {
        success {
            echo "✅ Build and deploy completed successfully."
            script {
                sendNotificationEmail('success')
                sh 'docker container prune -f'
                sh 'docker image prune -f'
                cleanWs()
            }
        }
        failure {
            script {
                echo "❌ Build failed in stage: ${env.CURRENT_STAGE}"
                sendNotificationEmail('failure')
                sh 'docker container prune -f'
                sh 'docker image prune -f'
                cleanWs()
            }
        }
    }
}

def versionCalculation() {
    sshagent(credentials: ['gitlabssh']) {
        sh "git remote set-url origin ${env.GIT_URL}"
        sh '''git fetch --tags'''
        def latestTag = sh(script: '''git tag | sort -V | tail -n1''', returnStdout: true).trim()
        echo "Latest tag is: ${latestTag}"

        def versionPattern = ~/^v?(\d+)\.(\d+)\.(\d+)$/
        def match = versionPattern.matcher(latestTag)

        if (latestTag && match.matches()) {
            echo "Incrementing patch version"
            def major = match.group(1).toInteger()
            def minor = match.group(2).toInteger()
            def patch = match.group(3).toInteger() + 1
            env.CALCULATED_VERSION = "v${major}.${minor}.${patch}"
        } else {
            echo "No existing tags or unrecognized format. Setting version to v1.0.0"
            env.CALCULATED_VERSION = "v1.0.0"
        }

        echo "Calculated version: ${env.CALCULATED_VERSION}"
    }
}

def sendNotificationEmail(String status) {
    def buildDuration = currentBuild.durationString.replace(' and counting', '')
    def deployedVersion = env.CALCULATED_VERSION ?: 'N/A'
    def currentStage = env.CURRENT_STAGE ?: 'Unknown'
    
    if (status == 'success') {
        emailext (
            to: "${env.NOTIFICATION_EMAIL}",
            subject: "✅ Pipeline Success - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
            mimeType: 'text/html',
            body: """
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .header { background-color: #28a745; color: white; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 20px; }
                    .info-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                    .info-table th, .info-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                    .info-table th { background-color: #f8f9fa; font-weight: bold; }
                    .success { color: #28a745; font-weight: bold; }
                    .footer { margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>🎉 Pipeline Completed Successfully!</h2>
                    </div>
                    
                    <table class="info-table">
                        <tr>
                            <th>Project:</th>
                            <td>${env.JOB_NAME}</td>
                        </tr>
                        <tr>
                            <th>Build Number:</th>
                            <td>#${env.BUILD_NUMBER}</td>
                        </tr>
                        <tr>
                            <th>Branch:</th>
                            <td>${env.BRANCH_NAME}</td>
                        </tr>
                        <tr>
                            <th>Status:</th>
                            <td class="success">✅ Success</td>
                        </tr>
                        <tr>
                            <th>Final Stage:</th>
                            <td>Deploy</td>
                        </tr>
                        <tr>
                            <th>Deployed Version:</th>
                            <td>${deployedVersion}</td>
                        </tr>
                        <tr>
                            <th>Duration:</th>
                            <td>${buildDuration}</td>
                        </tr>
                        <tr>
                            <th>Date:</th>
                            <td>${new Date().format('dd/MM/yyyy HH:mm')}</td>
                        </tr>
                    </table>
                    
                    <p>✅ <strong>Pipeline completed successfully</strong></p>
                    
                    <div class="footer">
                        <p>💡 View full details: <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                        <p>Sent from Jenkins CI/CD</p>
                    </div>
                </div>
            </body>
            </html>
            """
        )
    } else if (status == 'failure') {
        emailext (
            to: "${env.NOTIFICATION_EMAIL}",
            subject: "❌ Pipeline Failed - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
            mimeType: 'text/html',
            body: """
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .header { background-color: #dc3545; color: white; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 20px; }
                    .info-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                    .info-table th, .info-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                    .info-table th { background-color: #f8f9fa; font-weight: bold; }
                    .failure { color: #dc3545; font-weight: bold; }
                    .footer { margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }
                    .error-section { background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 15px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>🚨 Pipeline Failed!</h2>
                    </div>
                    
                    <table class="info-table">
                        <tr>
                            <th>Project:</th>
                            <td>${env.JOB_NAME}</td>
                        </tr>
                        <tr>
                            <th>Build Number:</th>
                            <td>#${env.BUILD_NUMBER}</td>
                        </tr>
                        <tr>
                            <th>Branch:</th>
                            <td>${env.BRANCH_NAME}</td>
                        </tr>
                        <tr>
                            <th>Status:</th>
                            <td class="failure">❌ Failed</td>
                        </tr>
                        <tr>
                            <th>Duration:</th>
                            <td>${buildDuration}</td>
                        </tr>
                        <tr>
                            <th>Date:</th>
                            <td>${new Date().format('dd/MM/yyyy HH:mm')}</td>
                        </tr>
                    </table>
                    
                    <div class="error-section">
                        <h3>🔍 Build Failed</h3>
                        <p><strong>Failed Stage:</strong> ${currentStage}</p>
                        <p>Please check the build logs for more details.</p>
                    </div>
                    
                    <p><strong>Recommended Actions:</strong></p>
                    <ul>
                        <li>🔍 Check full logs</li>
                        <li>🧪 Run local tests</li>
                        <li>🔄 Try running the pipeline again</li>
                        <li>👥 Contact development team if issue persists</li>
                    </ul>
                    
                    <div class="footer">
                        <p>💡 View full logs: <a href="${env.BUILD_URL}console">${env.BUILD_URL}console</a></p>
                        <p>Sent from Jenkins CI/CD</p>
                    </div>
                </div>
            </body>
            </html>
            """
        )
    }
}