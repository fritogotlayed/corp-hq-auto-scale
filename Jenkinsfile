node {
    agent any
    def app

    stage('Checkout') {
        steps {
            checkout scm
        }
    }

    stage('Test') {
        steps {
            echo 'Testing...'
            sh 'tox -r'
        }
    }

    stage('Build') {
        steps {
            app = docker.build("fritogotlayed/corp-hq-auto-scale")
        }
    }

    stage('Publish') {
        /* This does not appear to be working right now. Comment for the time being.
        when {
            branch 'master'
        }
        */
        docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-fritogotlayed') {
            app.push("${env.BUILD_NUMBER}")
            app.push("latest")
        }
    }

    stage('Cleanup'){
        steps {
            cleanWs()
        }
    }
}