#!/bin/bash
# Start Payment Gateway Proxy
# This script starts the proxy service with proper environment loading

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Payment Gateway Proxy${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file from .env.example:${NC}"
    echo "cp .env.example .env"
    echo "# Then edit .env with your credentials"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Display configuration
echo -e "\n${YELLOW}📋 Configuration:${NC}"
echo -e "   Kiosk ID: ${GREEN}${KIOSK_ID}${NC}"
echo -e "   Cloud URL: ${GREEN}${CLOUD_WS_URL}${NC}"
echo -e "   Local Gateway: ${GREEN}${LOCAL_GATEWAY_URL}${NC}"
echo -e "   Log Level: ${GREEN}${LOG_LEVEL}${NC}"

# Start proxy
echo -e "\n${GREEN}🔌 Starting proxy service...${NC}"
python3 proxy.py
