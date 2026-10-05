pipeline {
    agent {
        label 'linux'
    }

    environment {
        DOCKER_HUB_REPO = 'vermakshitij19/studybuddy'
        DOCKER_HUB_CREDENTIALS_ID = 'dockerhub-token'
        GITHUB_CREDENTIALS_ID = 'github-token'
        KUBECONFIG_CREDENTIALS_ID = 'config'
        ARGOCD_SERVER = '34.131.128.179:31704'
        ARGOCD_APP = 'study'
        TOOL_DIR = "${WORKSPACE}/.tools"
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scmGit(
                    branches: [[name: '*/main']],
                    extensions: [],
                    userRemoteConfigs: [[
                        credentialsId: "${GITHUB_CREDENTIALS_ID}",
                        url: 'https://github.com/vermakshitij19/STUDY-BUDDY-AI.git'
                    ]]
                )
            }
        }

        stage('Check for pipeline-generated commit') {
            steps {
                script {
                    def commitMessage = sh(
                        script: 'git log -1 --pretty=%B',
                        returnStdout: true
                    ).trim()
                    env.SKIP_PIPELINE = commitMessage.contains('[skip ci]') ? 'true' : 'false'
                }
            }
        }

        stage('Build Docker Image') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                script {
                    dockerImage = docker.build("${DOCKER_HUB_REPO}:${IMAGE_TAG}")
                }
            }
        }

        stage('Push Image to DockerHub') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                script {
                    docker.withRegistry('https://registry-1.docker.io', DOCKER_HUB_CREDENTIALS_ID) {
                        dockerImage.push()
                    }
                }
            }
        }

        stage('Update Deployment Image') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                sh '''
                    set -eu
                    sed -i -E \
                        's|^([[:space:]]*image:[[:space:]]*vermakshitij19/studybuddy:).*|\1'"${IMAGE_TAG}"'|' \
                        manifests/deployment.yaml
                    grep -Fq "image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}" manifests/deployment.yaml
                '''
            }
        }

        stage('Commit Deployment Image') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: GITHUB_CREDENTIALS_ID,
                    usernameVariable: 'GIT_USER',
                    passwordVariable: 'GIT_PASS'
                )]) {
                    sh '''
                        set -eu
                        git config user.name "vermakshitij19"
                        git config user.email "vermakshitij19@gmail.com"
                        git add manifests/deployment.yaml

                        if ! git diff --cached --quiet; then
                            git commit -m "Update image tag to ${IMAGE_TAG} [skip ci]"

                            cat > "$WORKSPACE/.git-askpass" <<'EOF'
#!/bin/sh
case "$1" in
    *Username*) printf '%s\n' "$GIT_USER" ;;
    *Password*) printf '%s\n' "$GIT_PASS" ;;
    *) exit 1 ;;
esac
EOF
                            chmod 700 "$WORKSPACE/.git-askpass"
                            trap 'rm -f "$WORKSPACE/.git-askpass"' EXIT
                            GIT_ASKPASS="$WORKSPACE/.git-askpass" \
                                GIT_TERMINAL_PROMPT=0 \
                                git push origin HEAD:main
                        fi
                    '''
                }
            }
        }

        stage('Install kubectl and Argo CD CLI') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                sh '''
                    set -eu
                    mkdir -p "$TOOL_DIR"

                    KUBECTL_VERSION="$(curl --fail --location --silent --show-error \
                        https://dl.k8s.io/release/stable.txt)"
                    curl --fail --location --silent --show-error \
                        "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
                        --output "$TOOL_DIR/kubectl"
                    curl --fail --location --silent --show-error \
                        https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64 \
                        --output "$TOOL_DIR/argocd"

                    chmod 700 "$TOOL_DIR/kubectl" "$TOOL_DIR/argocd"
                    "$TOOL_DIR/kubectl" version --client
                    "$TOOL_DIR/argocd" version --client
                '''
            }
        }

        stage('Sync Application with Argo CD') {
            when {
                expression { env.SKIP_PIPELINE != 'true' }
            }
            steps {
                withCredentials([file(
                    credentialsId: config,
                    variable: 'config'
                )]) {
                    sh '''
                        set -eu
                        ARGOCD_PASSWORD="$("$TOOL_DIR/kubectl" get secret -n argocd \
                            argocd-initial-admin-secret \
                            -o jsonpath='{.data.password}' | base64 --decode)"
                        test -n "$ARGOCD_PASSWORD"

                        "$TOOL_DIR/argocd" login "$ARGOCD_SERVER" \
                            --username admin \
                            --password "$ARGOCD_PASSWORD" \
                            --insecure
                        "$TOOL_DIR/argocd" app sync "$ARGOCD_APP"
                    '''
                }
            }
        }
    }
}
