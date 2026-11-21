#!/bin/bash

cd "$(dirname "$0")" || exit 1
source .build/setenv.sh || exit 1


_TARGET=build
_VERBOSE=

usage() {
    cat <<EOF

Usage: $0 [TARGET] [OPTION]
    TARGET          analyze|build|clean|compile|package|rebuild|release|test|test-live
    OPTION
        --log       Creates an extensive build.log file
        --help      Shows this help
EOF
}

error() {
    echo
    echo -e "\033[0;31m${1}\033[0m ${2}"
}

failed() {
    echo
    echo -e "\033[41m                                                                                \033[0m"
    echo -e "\033[1;41mThe build failed                                                                \033[0m"
    echo -e "\033[41m                                                                                \033[0m"

    exit 1
}

# Parse command line argument values
# Note: Currently, last one on the command line wins (ex: rebuild clean == clean)
for i in "$@"; do
    case $1 in
        analyze|build|compile|package|rebuild|release|test|test-live) _TARGET=$1 ;;
        clean) _TARGET=clean; rm -rf .venv/ ;;
        -l|--log) _VERBOSE=verbose ;;
        --help) usage; exit 0 ;;
        *) error "Unknown option" "$1"; usage; failed ;;
    esac
    shift
done



uv sync --upgrade || failed
echo
uv run --no-sync invoke $_VERBOSE $_TARGET || failed
