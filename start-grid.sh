#!/bin/bash
GRID="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/grid.sh"
jsub -mem 200m -N thanatos $GRID
