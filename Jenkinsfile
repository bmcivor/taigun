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
                sh './scripts/test.sh'
            }
        }
    }

    post {
        always {
            sh 'docker compose down -v --remove-orphans || true'
            sh 'docker rmi taigun-docs:${BUILD_NUMBER} || true'
        }
    }
}
