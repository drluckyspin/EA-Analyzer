#!/bin/bash

# Test script for EA-Analyzer CLI Driver
# This script demonstrates the CLI functionality

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    echo
    echo -e "${BLUE}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_header "EA-Analyzer CLI Test Suite"

# Test 1: Check prerequisites
print_header "Test 1: Prerequisites Check"
./ea-analyzer-cli.sh check
print_success "Prerequisites check completed"

# Test 2: Show help
print_header "Test 2: Help Display"
./ea-analyzer-cli.sh help | head -20
print_success "Help display completed"

# Test 3: Show data summary
print_header "Test 3: Data Summary"
./ea-analyzer-cli.sh summary
print_success "Data summary completed"

# Test 4: Test custom query (without Neo4j)
print_header "Test 4: Custom Query Test"
print_info "Testing query command (will fail without Neo4j, but should show proper error handling)"
./ea-analyzer-cli.sh query "MATCH (n) RETURN n LIMIT 1" || true
print_success "Query command test completed"

# Test 5: Test configuration options
print_header "Test 5: Configuration Options"
print_info "Testing with custom data file option"
./ea-analyzer-cli.sh --data-file data/one-line-knowledge-graph.json summary
print_success "Configuration options test completed"

print_header "CLI Test Suite Completed"
print_success "All basic CLI functionality tests passed!"
print_info "To test Neo4j functionality, run: ./ea-analyzer-cli.sh demo"
