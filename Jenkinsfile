pipeline {
    agent any

    tools {
        maven 'maven-3.9'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        MAVEN_OPTS = '-Dmaven.test.skip=true'
        JAVA_TOOL_OPTIONS = '-Dfile.encoding=UTF-8' 
        JENKINS_NODE_COOKIE = 'dontKillMe'
    }

    stages {
        stage('Build Backend') {
            steps {
                sh 'cd backend-java && mvn -B clean package -DskipTests'
            }
        }

        stage('Deploy Locally') {
            steps {
                script {
                    def services = ['gateway-service', 'user-service', 'drilling-service']

                    for (svc in services) {
                        sh """
                            PID=\$(ps -ef | grep 'java' | grep '${svc}' | grep -v grep | awk '{print \$2}') || true
                            if [ ! -z "\$PID" ]; then
                                echo "Stopping old process for ${svc} (PID: \$PID)..."
                                kill -15 \$PID || kill -9 \$PID
                                sleep 2
                            fi
                        """
                        sh """
                            echo "Starting ${svc} on local Linux..."
                            cd backend-java/${svc}/target
                            
                            # 使用 nohup 丢到后台运行，日志输出到各自的 nohup.out 中
                            nohup java -jar ${svc}-*.jar > nohup.out 2>&1 &
                        """
                    }
                }
            }
        }
    }
}
