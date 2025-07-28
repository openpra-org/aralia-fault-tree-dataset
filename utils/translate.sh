#!/bin/bash

for model in $(ls -A openpsa); do
    ../utils/psa2xfta2.py openpsa/${model} xfta2/${model}
done
