#!/bin/bash

export PYTHONPATH=$(pwd)/tools:$PYTHONPATH
echo $PYTHONPATH

benchexec xfta2.xml @local.cfg
