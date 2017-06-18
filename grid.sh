#!/bin/bash

# Set time zone
export TZ="/usr/share/zoneinfo/Europe/Helsinki"

# Set locale
export LANGUAGE="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"
export PYTHONIOENCODING=UTF-8

# Start thanatos
THANATOS="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/thanatos.py"
$THANATOS
