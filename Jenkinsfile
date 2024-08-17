pipeline {
    agent any
    tools {
        nodejs 'node'
    }
    stages {
        stage('Lint commit messages') {
            steps {
                sh '''
                    fromCommit=$(git rev-parse origin/main)
                    npm install --save-dev @commitlint/config-conventional @commitlint/cli
                    npx commitlint --from=${fromCommit} --to=HEAD --verbose
                '''
            }
        }
    }
}
