pipeline {
    agent {
        docker {
            image 'python:2.7'
            label 'docker'
            args '-v /usr/bin/docker:/usr/bin/docker -v /var/run/docker.sock:/var/run/docker.sock -v ${HOME}/.docker:${WORKSPACE}/.docker'
        }
    }

    environment {
        DOCKER_REPOSITORY = 'registry.v0rt3x.ru/velovec'
        DOCKER_CONFIG = "${env.WORKSPACE}/.docker"
        RELEASE_VERSION = '1.0.0'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '15', daysToKeepStr: '30'))
    }

    stages {
        stage ('Build :: Set Version') {
            steps {
                script {
                    env.BUILD_VERSION = "${env.RELEASE_VERSION}-${env.BUILD_TIMESTAMP}-${env.BUILD_NUMBER}"

                    currentBuild.displayName = "${env.BRANCH_NAME} - ${env.BUILD_VERSION}"
                }
            }
        }


        stage ('Build :: Build Artifacts') {
            steps {
                sh 'docker build -t ${DOCKER_REPOSITORY}/fullpless-bot:${BUILD_VERSION} .'
            }
        }

        stage ('Promote') {
            when {
                branch 'master'
            }

            steps {
                sh 'docker push ${DOCKER_REPOSITORY}/fullpless-bot:${BUILD_VERSION}'
            }
        }
    }

    post {
        always {
            sh 'docker rmi $(docker images | grep ${BUILD_VERSION} | awk \'{ print $3 }\')'

            deleteDir()
        }
    }
}