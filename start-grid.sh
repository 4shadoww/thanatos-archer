#!/bin/bash
GRID="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/grid.sh"
jsub -sync y -mem 200m -N $GRID
