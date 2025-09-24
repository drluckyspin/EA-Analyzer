#!/bin/bash

# Check if colors are supported
if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors)" -ge 8 ]; then
    # Colors
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    # No colors
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

echo -e "${BLUE}Checking health of EA-Analyzer services${NC}"
echo ""
echo -e "${BLUE}Current Configuration:${NC}"
echo "  ENVIRONMENT=local"
echo "  NEO4J_URI=${NEO4J_URI:-bolt://localhost:7687}"
echo ""
echo -e "${BLUE}Infrastructure Services:${NC}"
echo -e "  • Neo4j (Graph Database - LOCAL): ${BLUE}http://localhost:7474${NC}"

neo4j_ok=0
if ./ea-analyzer-cli.sh db ping >/dev/null 2>&1; then
    echo -e "    ${GREEN}✓${NC} Neo4j is healthy"
    neo4j_ok=1
else
    echo -e "    ${RED}✗${NC} Neo4j is not responding"
fi

echo ""
echo -e "${BLUE}Application Services:${NC}"
echo -e "  • Frontend (Next.js): ${BLUE}http://localhost:3000${NC}"

frontend_ok=0
if curl -s -I http://localhost:3000 >/dev/null 2>&1; then
    echo -e "    ${GREEN}✓${NC} Frontend is healthy"
    frontend_ok=1
else
    echo -e "    ${RED}✗${NC} Frontend is not responding"
fi

echo -e "  • Backend API (FastAPI): ${BLUE}http://localhost:8000${NC}"

backend_ok=0
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "    ${GREEN}✓${NC} Backend API is healthy"
    backend_ok=1
else
    echo -e "    ${RED}✗${NC} Backend API is not responding"
fi

echo ""
if [ "$neo4j_ok" = "1" ] && [ "$frontend_ok" = "1" ] && [ "$backend_ok" = "1" ]; then
    echo -e "${GREEN}Health check complete!${NC}"
    exit 0
else
    echo -e "${RED}Health check complete!${NC}"
    echo ""
    echo -e "${YELLOW}To start all services: make run-web${NC}"
    echo -e "${YELLOW}To start only Neo4j: make start${NC}"
    exit 1
fi
