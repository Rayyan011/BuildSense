#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if username and repo URL are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    print_error "Please provide your Uberspace username and repository URL"
    echo "Usage: $0 <uberspace_username> <repository_url>"
    echo "Example: $0 rayyan https://github.com/yourusername/buildsense.git"
    exit 1
fi

UBERSPACE_USER=$1
REPO_URL=$2
DEPLOY_DIR="/home/${UBERSPACE_USER}/buildsense"
APP_NAME="buildsense"
DOMAIN="${APP_NAME}.${UBERSPACE_USER}.uber.space"
PORT=7862

print_message "Starting deployment process for BuildSense to Uberspace..."

# 1. SSH into Uberspace and execute deployment commands
print_message "Connecting to Uberspace and setting up the environment..."
ssh ${UBERSPACE_USER}@${UBERSPACE_USER}.uber.space << EOF
    # Create or clean deployment directory
    if [ -d "${DEPLOY_DIR}" ]; then
        print_message "Cleaning existing deployment directory..."
        rm -rf ${DEPLOY_DIR}
    fi
    mkdir -p ${DEPLOY_DIR}
    cd ${DEPLOY_DIR}

    # Clone the repository
    print_message "Cloning repository from ${REPO_URL}..."
    git clone ${REPO_URL} .

    # Set up Python virtual environment
    print_message "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Configure web server
    print_message "Configuring web server..."
    uberspace web backend set / --http --port ${PORT}

    # Set up systemd service
    print_message "Setting up systemd service..."
    cat > ~/etc/services.d/${APP_NAME}.ini << EOL
[program:${APP_NAME}]
command=${DEPLOY_DIR}/venv/bin/python app.py --port ${PORT}
directory=${DEPLOY_DIR}
user=%(ENV_USER)s
autostart=1
autorestart=1
redirect_stderr=1
stdout_logfile=%(ENV_HOME)s/logs/${APP_NAME}.log
EOL

    # Configure reverse proxy
    print_message "Configuring reverse proxy..."
    uberspace web backend set / --http --port ${PORT}
    uberspace web domain add ${DOMAIN}
    uberspace web domain set ${DOMAIN} --backend /

    # Enable service to start on boot
    print_message "Enabling service to start on boot..."
    supervisord -c ~/etc/supervisord.conf
    supervisorctl reread
    supervisorctl update
    supervisorctl start ${APP_NAME}

    print_message "Deployment completed successfully!"
    print_message "Your application should be available at: https://${DOMAIN}"
EOF

print_message "Deployment process completed!"
print_message "Please check https://${DOMAIN} to verify your application is running."
print_message "If you encounter any issues, check the logs at: ~/logs/${APP_NAME}.log" 