#!/bin/bash
# Convenient script to run tests in virtual environment

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Fashion Backend Test Runner with Virtual Environment${NC}"
echo "=================================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
echo -e "${YELLOW}🔄 Checking dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies are up to date${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📋 Available test commands:${NC}"
echo "  ./test.sh unit          - Run unit tests (fast)"
echo "  ./test.sh integration   - Run integration tests (requires server)"
echo "  ./test.sh performance   - Run performance tests"
echo "  ./test.sh coverage      - Run unit tests with coverage"
echo "  ./test.sh api           - Run API tests only"
echo "  ./test.sh service       - Run service tests only"
echo "  ./test.sh model         - Run model tests only"
echo ""

# Run tests based on argument
case "$1" in
    "unit")
        echo -e "${BLUE}🏃 Running unit tests...${NC}"
        python run_tests.py --unit
        ;;
    "integration")
        echo -e "${BLUE}🏃 Running integration tests...${NC}"
        echo -e "${YELLOW}⚠️  Make sure the API server is running: uvicorn main:app --reload${NC}"
        python run_tests.py --integration
        ;;
    "performance")
        echo -e "${BLUE}🏃 Running performance tests...${NC}"
        python run_tests.py --performance
        ;;
    "coverage")
        echo -e "${BLUE}🏃 Running unit tests with coverage...${NC}"
        python run_tests.py --unit --coverage-html
        echo -e "${GREEN}📊 Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "api")
        echo -e "${BLUE}🏃 Running API tests...${NC}"
        python run_tests.py --api
        ;;
    "service")
        echo -e "${BLUE}🏃 Running service tests...${NC}"
        python run_tests.py --service
        ;;
    "model")
        echo -e "${BLUE}🏃 Running model tests...${NC}"
        python run_tests.py --model
        ;;
    "")
        echo -e "${BLUE}🏃 Running all tests (excluding slow ones)...${NC}"
        python run_tests.py
        ;;
    *)
        echo -e "${RED}❌ Unknown test type: $1${NC}"
        echo "Use one of: unit, integration, performance, coverage, api, service, model"
        exit 1
        ;;
esac
