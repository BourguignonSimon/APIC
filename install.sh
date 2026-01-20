#!/bin/bash
# APIC Installation Script
# Handles package installation with retry logic for network issues

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAX_RETRIES=3
RETRY_DELAY=5
PIP_TIMEOUT=300

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}APIC Installation Script${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${RED}Error: Python 3.11 or higher is required${NC}"
    echo -e "${RED}Current version: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
    echo -e "${YELLOW}It's recommended to use a virtual environment${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Creating virtual environment...${NC}"
        python -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
        echo -e "${YELLOW}Please activate it with: source venv/bin/activate${NC}"
        echo -e "${YELLOW}Then run this script again${NC}"
        exit 0
    fi
else
    echo -e "${GREEN}✓ Virtual environment activated: $VIRTUAL_ENV${NC}"
fi
echo ""

# Upgrade pip, setuptools, and wheel first
echo -e "${BLUE}Upgrading pip, setuptools, and wheel...${NC}"
python -m pip install --upgrade pip setuptools wheel --timeout $PIP_TIMEOUT
echo -e "${GREEN}✓ Core tools upgraded${NC}"
echo ""

# Function to install packages with retry logic
install_with_retry() {
    local requirements_file=$1
    local attempt=1

    echo -e "${BLUE}Installing packages from $requirements_file...${NC}"

    while [ $attempt -le $MAX_RETRIES ]; do
        echo -e "${BLUE}Attempt $attempt of $MAX_RETRIES${NC}"

        # Use pip configuration file if it exists
        if [ -f "pip.conf" ]; then
            export PIP_CONFIG_FILE="pip.conf"
        fi

        # Try to install with increased timeout and retries
        if pip install -r "$requirements_file" \
            --timeout $PIP_TIMEOUT \
            --retries 5 \
            --default-timeout $PIP_TIMEOUT \
            2>&1 | tee /tmp/pip_install.log; then
            echo -e "${GREEN}✓ Successfully installed packages from $requirements_file${NC}"
            return 0
        else
            echo -e "${YELLOW}Installation failed on attempt $attempt${NC}"

            # Check if it's a timeout error
            if grep -q "TimeoutError\|timed out\|Connection refused" /tmp/pip_install.log; then
                echo -e "${YELLOW}Network timeout detected${NC}"
            fi

            if [ $attempt -lt $MAX_RETRIES ]; then
                echo -e "${YELLOW}Waiting ${RETRY_DELAY} seconds before retry...${NC}"
                sleep $RETRY_DELAY
                # Exponential backoff
                RETRY_DELAY=$((RETRY_DELAY * 2))
            fi
        fi

        attempt=$((attempt + 1))
    done

    echo -e "${RED}Failed to install packages after $MAX_RETRIES attempts${NC}"
    return 1
}

# Install production dependencies
if [ -f "requirements.txt" ]; then
    if install_with_retry "requirements.txt"; then
        echo ""
    else
        echo -e "${RED}Installation failed. Please check your network connection and try again.${NC}"
        echo -e "${YELLOW}You can also try installing packages one by one manually.${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi

# Ask about development dependencies
if [ -f "requirements-dev.txt" ]; then
    echo ""
    read -p "Install development dependencies? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if install_with_retry "requirements-dev.txt"; then
            echo ""
        else
            echo -e "${YELLOW}Warning: Development dependencies installation failed${NC}"
            echo -e "${YELLOW}You can try installing them later manually${NC}"
        fi
    fi
fi

# Verify installation
echo ""
echo -e "${BLUE}Verifying installation...${NC}"
if [ -f "src/utils/install_verifier.py" ]; then
    python -m src.utils.install_verifier
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Installation verification passed${NC}"
    else
        echo -e "${YELLOW}Warning: Some verification checks failed${NC}"
        echo -e "${YELLOW}The installation may still work, but some features might be unavailable${NC}"
    fi
else
    echo -e "${YELLOW}Verification script not found, skipping...${NC}"
fi

echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Copy .env.example to .env and configure your API keys"
echo -e "2. Start the application with: python main.py api"
echo -e "3. In another terminal, run: python main.py frontend"
echo ""
