pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    parameters {
        string(name: 'REGISTRY', defaultValue: 'welllog', description: 'Docker registry / namespace, e.g. your-registry/welllog')
        string(name: 'IMAGE_TAG', defaultValue: '', description: 'Image tag, empty uses BUILD_NUMBER')
        string(name: 'KUBE_NAMESPACE', defaultValue: 'welllog', description: 'Kubernetes namespace')
        string(name: 'KUBECONFIG_CREDENTIALS_ID', defaultValue: 'kubeconfig-welllog', description: 'Jenkins credentials id for kubeconfig file')
        booleanParam(name: 'APPLY_K8S', defaultValue: true, description: 'Apply Kubernetes manifests after image push')
    }

    environment {
        MAVEN_OPTS = '-Dmaven.test.skip=true'
        JAVA_TOOL_OPTIONS = '-Dfile.encoding=UTF-8'
    }

    stages {
        stage('Prepare') {
            steps {
                script {
                    env.IMAGE_TAG_FINAL = params.IMAGE_TAG?.trim() ? params.IMAGE_TAG.trim() : "${env.BUILD_NUMBER}"
                    env.IMAGE_PREFIX = "${params.REGISTRY}".replaceAll('/$', '')
                }
            }
        }

        stage('Build Backend') {
            steps {
                sh 'cd backend-java && mvn -B clean package -DskipTests'
            }
        }

        stage('Build Images') {
            steps {
                script {
                    def services = ['gateway-service', 'user-service', 'drilling-service']
                    for (svc in services) {
                        sh "docker build -f backend-java/${svc}/Dockerfile -t ${env.IMAGE_PREFIX}/${svc}:${env.IMAGE_TAG_FINAL} -t ${env.IMAGE_PREFIX}/${svc}:latest backend-java"
                    }
                }
            }
        }

        stage('Push Images') {
            steps {
                script {
                    def services = ['gateway-service', 'user-service', 'drilling-service']
                    for (svc in services) {
                        sh "docker push ${env.IMAGE_PREFIX}/${svc}:${env.IMAGE_TAG_FINAL}"
                        sh "docker push ${env.IMAGE_PREFIX}/${svc}:latest"
                    }
                }
            }
        }

        stage('Render K8s Manifests') {
            steps {
                sh '''
                    set -eu
                    rm -rf target/k8s-rendered
                    mkdir -p target/k8s-rendered
                    cp backend-java/k8s/* target/k8s-rendered/

                    for svc in gateway-service user-service drilling-service; do
                      sed -i "s|image: welllog/${svc}:latest|image: ${IMAGE_PREFIX}/${svc}:${IMAGE_TAG_FINAL}|g" target/k8s-rendered/${svc}.yaml
                    done
                '''
            }
        }

        stage('Deploy to K8s') {
            when {
                expression { return params.APPLY_K8S }
            }
            steps {
                withCredentials([file(credentialsId: params.KUBECONFIG_CREDENTIALS_ID, variable: 'KUBECONFIG_FILE')]) {
                    sh """
                        set -eu
                        export KUBECONFIG='${KUBECONFIG_FILE}'
                        namespace='${params.KUBE_NAMESPACE}'

                        kubectl apply -f target/k8s-rendered/namespace.yaml
                        kubectl apply -f target/k8s-rendered/consul.yaml -n "\$namespace"
                        kubectl apply -f target/k8s-rendered/user-service.yaml -n "\$namespace"
                        kubectl apply -f target/k8s-rendered/drilling-service.yaml -n "\$namespace"
                        kubectl apply -f target/k8s-rendered/gateway-service.yaml -n "\$namespace"
                        kubectl apply -f target/k8s-rendered/ingress.yaml -n "\$namespace"

                        kubectl rollout restart deployment/user-service -n "\$namespace"
                        kubectl rollout restart deployment/drilling-service -n "\$namespace"
                        kubectl rollout restart deployment/gateway-service -n "\$namespace"

                        kubectl rollout status deployment/user-service -n "\$namespace" --timeout=180s
                        kubectl rollout status deployment/drilling-service -n "\$namespace" --timeout=180s
                        kubectl rollout status deployment/gateway-service -n "\$namespace" --timeout=180s
                    """
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'target/k8s-rendered/**', allowEmptyArchive: true
        }
    }
}
