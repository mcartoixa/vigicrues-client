#!/bin/bash

error() {
    echo
    echo -e "\033[0;31m${1}\033[0m" >&2
}

# Git must be on the PATH for pygount (through GitPython)
if ! git --version; then
    error "Could not find Git"
    return 1
fi
if ! uv --version; then
    error "Could not find uv"
    return 1
fi
echo



if [ -f ./.env ]; then
    # xargs does not support the -d option on BSD (MacOS X)
    export $(grep -a -v -e '^#' -e '^[[:space:]]*$' .env | tr '\n' '\0' | xargs -0 )
    grep -a -v -e '^#' -e '^[[:space:]]*$' .env | tr '\n' '\0' | xargs -0 printf "\$%s\n"
    echo
fi
