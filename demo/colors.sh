#!/bin/bash

# Check if we have colors enabled
tput=$(which tput)
if [ -n "$tput" ]; then
    ncolors=$($tput colors)
    if [ -n "$ncolors" ] && [ "$ncolors" -ge 8 ]; then
        black="$(tput setaf 0)"
        red="$(tput setaf 1)"
        green="$(tput setaf 2)"
        white="$(tput setaf 7)"
        whitebg="$(tput setab 7)"
        greenbg="$(tput setab 2)"
        redbg="$(tput setab 1)"
        reset="$(tput sgr0)"
    else
        black=""
        red=""
        green=""
        white=""
        whitebg=""
        greenbg=""
        redbg=""
        reset=""
    fi
fi
