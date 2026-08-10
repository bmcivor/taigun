pipeline {
    agent any

    stages {
        stage('Docs') {
            steps {
                sh 'docker build --target docs -t taigun-docs:${BUILD_NUMBER} .'
                sh 'docker run --rm taigun-docs:${BUILD_NUMBER} build --strict'
            }
        }
        stage('Test') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    sh './scripts/test.sh'
                }
            }
        }
        stage('Lint') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    sh './scripts/lint.sh'
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'junit.xml'
            sh 'docker compose down -v --remove-orphans || true'
            sh 'docker rmi taigun-docs:${BUILD_NUMBER} || true'
        }
    }
}
