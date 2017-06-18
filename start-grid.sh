#!/bin/bash
GRID="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/grid.sh"
jsub -mem 500m -N thanatos $GRID
