#!/bin/bash

# -----------------------------------------------------------------------------
# Script Name: log.bash
# Usage: source log.bash
#
# Description: A collection of logging utility functions for bash scripts that
#              provide colored and formatted console output.
#
# Functions:
#   get_terminal_width : Get current terminal width (max 120 chars)
#   log                : Basic white text logging
#   log_dim            : Dimmed white text logging
#   log_info           : Dimmed blue text for info messages
#   log_error          : Dimmed red text for error messages
#   log_warning        : Dimmed yellow text for warnings
#   log_separator      : Print a separator line across terminal width
#   log_centered       : Print centered text
#   log_verbose        : Log message only if VERBOSE environment variable is true
# -----------------------------------------------------------------------------

# ANSI color codes
RED='\033[91m'
# shellcheck disable=SC2034
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
WHITE='\033[97m'
RESET='\033[0m'
DIM='\033[2m'


# Get terminal width (max 120)
get_terminal_width() {
    local width
    width=$(tput cols)
    if [ "$width" -gt 120 ]; then
        width=120
    fi
    echo "$width"
}

# Basic logging functions
log() {
    echo -e "${WHITE} $1${RESET}"
}

log_dim() {
    echo -e "${DIM}${WHITE} $1${RESET}"
}

log_info() {
    echo -e "${BLUE} $1${RESET}"
}

log_info_dim() {
    echo -e "${DIM}${BLUE} $1${RESET}"
}

log_error() {
    echo -e "${DIM}${RED} $1${RESET}"
}

log_warning() {
    echo -e "${DIM}${YELLOW} $1${RESET}"
}

log_separator() {
    local width
    width=$(get_terminal_width)
    printf "=-%.0s" $(seq 1 $((width / 2)))
    echo "="
}

log_centered() {
    local width
    local message="$1"
    width=$(get_terminal_width)

    # Calculate padding
    local padding=$(((width - ${#message}) / 2))

    # Create padding string
    local pad_str
    pad_str=$(printf '%*s' "$padding" '')

    # Print centered message
    echo -e "${pad_str}${message}"
}

log_verbose() {
    if [[ "${VERBOSE:-false}" == "true" ]]; then
        log_info_dim "$*"
    fi
}

log_banner() {

    # Show script banner - Ad Astra logo. This gives us color in the console and is fun.
echo -e "    
███████╗ █████╗      █████╗ ███╗   ██╗ █████╗ ██╗  ██╗   ██╗███████╗███████╗██████╗ 
██╔════╝██╔══██╗    ██╔══██╗████╗  ██║██╔══██╗██║  ╚██╗ ██╔╝╚══███╔╝██╔════╝██╔══██╗
█████╗  ███████║    ███████║██╔██╗ ██║███████║██║   ╚████╔╝   ███╔╝ █████╗  ██████╔╝
██╔══╝  ██╔══██║    ██╔══██║██║╚██╗██║██╔══██║██║    ╚██╔╝   ███╔╝  ██╔══╝  ██╔══██╗
███████╗██║  ██║    ██║  ██║██║ ╚████║██║  ██║███████╗██║   ███████╗███████╗██║  ██║
╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═╝   ╚══════╝╚══════╝╚═╝  ╚═╝
                                                     .. a ${RED}Bain${RESET} AI Innovation Project"
}

# Example usage
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    log_separator
    log_banner
    log "This is a normal message."
    log_dim "This is a dim message."
    log_info "This is an info message."
    log_warning "This is a warning message."
    log_error "This is an error message."
    log_centered "This is a centered message"
    log_separator
fi
