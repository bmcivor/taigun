pipeline {
    agent any

    stages {
        stage('Docs') {
            steps {
                sh 'docker run --rm -v "$PWD":/docs:ro squidfunk/mkdocs-material:9.7.1 build --strict -d /tmp/site'
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
        }
    }
}
