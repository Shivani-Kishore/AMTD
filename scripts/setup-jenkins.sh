#!/bin/bash
# AMTD Jenkins Setup Script
# Configures Jenkins for AMTD scanning

set -e

echo "=========================================="
echo "AMTD Jenkins Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Jenkins URL (can be overridden with environment variable)
JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JENKINS_USER="${JENKINS_ADMIN_USER:-admin}"
JENKINS_PASSWORD="${JENKINS_ADMIN_PASSWORD:-admin123}"

echo "Jenkins URL: $JENKINS_URL"

# Function to wait for Jenkins to be ready
wait_for_jenkins() {
    echo "Waiting for Jenkins to be ready..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$JENKINS_URL/login" > /dev/null 2>&1; then
            echo -e "${GREEN}Jenkins is ready!${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "Attempt $attempt/$max_attempts..."
        sleep 10
    done

    echo -e "${RED}Jenkins failed to start within timeout${NC}"
    return 1
}

# Function to install Jenkins plugins
install_plugins() {
    echo "=========================================="
    echo "Installing Jenkins Plugins"
    echo "=========================================="

    local plugins=(
        "workflow-aggregator"
        "pipeline-stage-view"
        "git"
        "github"
        "docker-workflow"
        "email-ext"
        "slack"
        "html-publisher"
        "credentials-binding"
        "job-dsl"
        "configuration-as-code"
    )

    for plugin in "${plugins[@]}"; do
        echo "Installing plugin: $plugin"
        curl -X POST "$JENKINS_URL/pluginManager/installNecessaryPlugins" \
            --user "$JENKINS_USER:$JENKINS_PASSWORD" \
            -d "<install plugin='$plugin@latest' />" \
            -H 'Content-Type: text/xml' || true
    done

    echo -e "${GREEN}Plugins installation initiated${NC}"
    echo "Note: Plugins will install in the background. Restart Jenkins when complete."
}

# Function to create AMTD scan job
create_scan_job() {
    echo "=========================================="
    echo "Creating AMTD Scan Job"
    echo "=========================================="

    local job_config='<?xml version="1.0" encoding="UTF-8"?>
<flow-definition plugin="workflow-job">
  <description>AMTD Security Scanning Pipeline</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>APPLICATION</name>
          <defaultValue>juice-shop</defaultValue>
          <description>Application to scan</description>
        </hudson.model.StringParameterDefinition>
        <hudson.model.ChoiceParameterDefinition>
          <name>SCAN_TYPE</name>
          <choices>
            <string>full</string>
            <string>quick</string>
            <string>incremental</string>
          </choices>
          <description>Type of scan to perform</description>
        </hudson.model.ChoiceParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>https://github.com/your-org/amtd.git</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/main</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>'

    echo "$job_config" | curl -X POST "$JENKINS_URL/createItem?name=amtd-scan" \
        --user "$JENKINS_USER:$JENKINS_PASSWORD" \
        -H "Content-Type: application/xml" \
        -d @-

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}AMTD Scan job created successfully${NC}"
    else
        echo -e "${YELLOW}Job may already exist or creation failed${NC}"
    fi
}

# Function to configure credentials
configure_credentials() {
    echo "=========================================="
    echo "Credential Configuration"
    echo "=========================================="

    echo "Please configure the following credentials in Jenkins:"
    echo "1. Navigate to: $JENKINS_URL/credentials/"
    echo "2. Add the following credentials:"
    echo ""
    echo "   - github-token (Secret text)"
    echo "     ID: github-token"
    echo "     Description: GitHub Personal Access Token"
    echo ""
    echo "   - slack-webhook-url (Secret text)"
    echo "     ID: slack-webhook-url"
    echo "     Description: Slack Webhook URL"
    echo ""
    echo "   - docker-credentials (Username with password)"
    echo "     ID: docker-credentials"
    echo "     Description: Docker registry credentials"
    echo ""
}

# Function to setup shared library
setup_shared_library() {
    echo "=========================================="
    echo "Shared Library Configuration"
    echo "=========================================="

    echo "To configure the AMTD shared library:"
    echo "1. Navigate to: $JENKINS_URL/configure"
    echo "2. Scroll to 'Global Pipeline Libraries'"
    echo "3. Click 'Add' and configure:"
    echo "   - Name: amtd-shared-library"
    echo "   - Default version: main"
    echo "   - Retrieval method: Modern SCM"
    echo "   - Source: Git"
    echo "   - Project Repository: https://github.com/your-org/amtd.git"
    echo ""
}

# Main execution
main() {
    echo "Starting Jenkins setup for AMTD..."

    # Wait for Jenkins
    if ! wait_for_jenkins; then
        exit 1
    fi

    # Install plugins
    echo ""
    read -p "Install Jenkins plugins? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_plugins
    fi

    # Create scan job
    echo ""
    read -p "Create AMTD scan job? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_scan_job
    fi

    # Display manual configuration steps
    echo ""
    configure_credentials
    echo ""
    setup_shared_library

    echo ""
    echo "=========================================="
    echo -e "${GREEN}Jenkins Setup Complete!${NC}"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Complete credential configuration (see above)"
    echo "2. Configure shared library (see above)"
    echo "3. Restart Jenkins: docker restart amtd-jenkins"
    echo "4. Run your first scan: $JENKINS_URL/job/amtd-scan/"
    echo ""
}

# Run main function
main "$@"
