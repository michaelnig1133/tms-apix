pipeline {
    agent any

    environment {
        REGISTRY = '199900000'  // Docker Hub username
        IMAGE_NAME = 'TMS'     // Docker image name
        IMAGE_TAG = 'lat'       // Version tag
        DOCKER_CREDENTIALS = 'gatepass_dockerhub'  // Jenkins credential ID for Docker login
        SONARQUBE_CREDENTIALS = 'gatepass_sonarqube'  // Jenkins credential ID for SonarQube
        SONARQUBE_URL = "http://sonar:9000"  // SonarQube server URL
        //PROJECT_KEY = "gatepassvms"  // Unique key for your SonarQube project
        EMAIL_RECIPIENTS = 'michaelnigusu030@gmail.com'
       
       
    }

    stages {

        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'git@github.com:michaelnig1133/tms-apix.git'
            }
        }

        stage('build') {
              steps{
                  script {
                      sh ''' #!/bin/bash
                        echo "Building Docker image..."
                        export COMPOSE_BAKE=true
                        docker compose up -d

                      '''
                  }
              }
        }

      
       
      
    }

    post {
        success {
            echo 'Deployment Successful!'
            emailext(
                subject: "Deployment Successful - TMS",
                body: "The TMS application has been successfully deployed.",
                to: "$EMAIL_RECIPIENTS",
                 attachLog: true
            )
        }
        failure {
            echo 'Deployment Failed. Check logs.'
            emailext(
                subject: "Deployment Failed -TMS",
                body: "The deployment has failed. Please check the Jenkins logs for details.",
                to: "$EMAIL_RECIPIENTS",
                attachLog: true
            )
        }
    }
}
