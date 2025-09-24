#!/bin/bash

# EA-Analyzer Simple CLI Wrapper
# A lightweight wrapper around the Typer-based CLI

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Load environment variables from .env file
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
    fi

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Ensure Python can import project modules from src/
SRC_DIR="$PROJECT_DIR/src"
if [ -d "$SRC_DIR" ]; then
    export PYTHONPATH="${SRC_DIR}${PYTHONPATH:+:$PYTHONPATH}"
fi

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print error message
print_error() {
    print_color $RED "✗ $1"
}

# Function to print success message
print_success() {
    print_color $GREEN "✓ $1"
}

# Function to print info message
print_info() {
    print_color $BLUE "ℹ $1"
}

# Function to get the Typer CLI command
get_typer_cmd() {
    echo "uv run --python .venv/bin/python -m ea_analyzer.typer_cli"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    local verbose="$1"
    
    if [ "$verbose" = "true" ]; then
        print_info "Checking prerequisites..."
    fi
    
    local missing_deps=()
    
    # Check for Python
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    # Check for uv
    if ! command_exists uv; then
        missing_deps+=("uv")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_info "Please install missing dependencies and try again"
        exit 1
    fi
    
    if [ "$verbose" = "true" ]; then
        print_success "Prerequisites satisfied"
    fi
}

# Function to show help
show_help() {
    echo
    print_color $BLUE "╭─────────────────────────────────────────────────────────────────────────────────╮"
    print_color $BLUE "│                           EA-Analyzer CLI Wrapper                               │"
    print_color $BLUE "╰─────────────────────────────────────────────────────────────────────────────────╯"
    echo
    print_color $YELLOW "A lightweight wrapper around the Typer-based EA-Analyzer CLI."
    echo
    echo
    print_color $YELLOW "USAGE:"
    print_color $WHITE "    $0 [COMMAND] [OPTIONS]"
    echo
    echo
    print_color $YELLOW "COMMANDS:"
    echo -e "${GREEN}    check${WHITE}               Check prerequisites and system status${NC}"
    echo -e "${GREEN}    summary${WHITE}             Show diagram summary from JSON file${NC}"
    echo -e "${GREEN}    store${WHITE}               Store diagram in database${NC}"
    echo -e "${GREEN}    analyze${WHITE}             Analyze electrical diagram image using LLM${NC}"
    echo -e "${GREEN}    db${WHITE}                  Database operations (use 'db --help')${NC}"
    echo -e "${GREEN}    examples${WHITE}            Run example queries${NC}"
    echo -e "${GREEN}    demo${WHITE}                Run complete demo${NC}"
    echo -e "${GREEN}    help${WHITE}                Show this help message${NC}"
    echo
    echo
    print_color $YELLOW "OPTIONS:"
    echo -e "${PURPLE}    --data-file FILE${WHITE}    Path to JSON data file${NC}"
    echo -e "${PURPLE}    --db-type TYPE${WHITE}      Database type (neo4j, postgres, etc.)${NC}"
    echo -e "${PURPLE}    --db-uri URI${WHITE}        Database connection URI${NC}"
    echo -e "${PURPLE}    --db-user USER${WHITE}      Database username${NC}"
    echo -e "${PURPLE}    --db-pass PASS${WHITE}      Database password${NC}"
    echo -e "${PURPLE}    --db-name DB${WHITE}        Database name${NC}"
    echo -e "${PURPLE}    --verbose, -v${WHITE}       Enable verbose output${NC}"
    echo -e "${PURPLE}    --typer-help${WHITE}        Show Typer CLI help output${NC}"
    echo
    echo
    print_color $YELLOW "EXAMPLES:"
    print_color $WHITE "    $0 check"
    print_color $WHITE "    $0 summary"
    print_color $WHITE "    $0 store"
    print_color $WHITE "    $0 analyze substation.png"
    print_color $WHITE "    $0 analyze substation.png --output custom.json --store"
    print_color $WHITE "    $0 db summary"
    print_color $WHITE "    $0 db protection-schemes"
    print_color $WHITE "    $0 db query \"MATCH (n:Transformer) RETURN n.name\""
    print_color $WHITE "    $0 demo"
    print_color $WHITE "    $0 --data-file custom-data.json store"
    print_color $WHITE "    $0 --typer-help"
    echo
    echo
    print_color $YELLOW "ENVIRONMENT VARIABLES:"
    echo -e "${CYAN}    DATA_FILE${WHITE}           Path to JSON data file${NC}"
    echo -e "${CYAN}    DB_TYPE${WHITE}             Database type (neo4j, postgres, etc.)${NC}"
    echo -e "${CYAN}    DB_URI${WHITE}              Database connection URI${NC}"
    echo -e "${CYAN}    DB_USERNAME${WHITE}        Database username${NC}"
    echo -e "${CYAN}    DB_PASSWORD${WHITE}        Database password${NC}"
    echo -e "${CYAN}    DB_DATABASE${WHITE}        Database name${NC}"
    echo -e "${CYAN}    LLM_PROVIDER${WHITE}        LLM provider (openai, anthropic, gemini)${NC}"
    echo -e "${CYAN}    LLM_MODEL${WHITE}           LLM model name${NC}"
    echo -e "${CYAN}    OPENAI_API_KEY${WHITE}      OpenAI API key${NC}"
    echo -e "${CYAN}    ANTHROPIC_API_KEY${WHITE}   Anthropic API key${NC}"
    echo -e "${CYAN}    GOOGLE_API_KEY${WHITE}      Google API key${NC}"
    echo
    echo
    print_color $YELLOW "QUICK START:"
    print_color $WHITE "    $0 check                    # Check required tools and system status"
    print_color $WHITE "    $0 analyze substation.png   # Analyze electrical diagram with LLM"
    print_color $WHITE "    $0 analyze substation.png --store  # Analyze and store in database"
    print_color $WHITE "    $0 db list                  # View stored diagrams"
    print_color $WHITE "    $0 db export 1              # Export diagram to PNG"
    print_color $WHITE "    $0 demo                     # Run complete demo"
    echo
    echo
    print_color $YELLOW "For more detailed help on specific commands:"
    print_color $WHITE "    $0 [COMMAND] --help"
    print_color $WHITE "    $0 db --help"
    echo
}

# Main function
main() {
    # Check if no arguments provided
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # Check for help flags
    if [[ "$1" == "help" || "$1" == "--help" || "$1" == "-h" ]]; then
        show_help
        exit 0
    fi
    
    # Check for typer help flag
    if [[ "$1" == "--typer-help" ]]; then
        local typer_cmd="$(get_typer_cmd)"
        eval "$typer_cmd --help"
        exit 0
    fi
    
    # Check if verbose flag is present
    local verbose="false"
    for arg in "$@"; do
        if [[ "$arg" == "--verbose" || "$arg" == "-v" ]]; then
            verbose="true"
            break
        fi
    done
    
    # Check prerequisites for most commands
    if [[ "$1" != "help" && "$1" != "--help" && "$1" != "-h" ]]; then
        check_prerequisites "$verbose"
    fi
    
    # Get the Typer CLI command
    local typer_cmd="$(get_typer_cmd)"
    
    # Pass all arguments to the Typer CLI
    eval "$typer_cmd $*"
}

# Run main function with all arguments
main "$@"
