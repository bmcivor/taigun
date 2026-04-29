pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh 'docker build --target test -t taigun-test:${BUILD_NUMBER} .'
                sh 'docker run --rm taigun-test:${BUILD_NUMBER} uv run pytest tests/ -v'
            }
        }
    }

    post {
        always {
            sh 'docker rmi taigun-test:${BUILD_NUMBER} || true'
        }
    }
}
