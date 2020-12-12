#!/bin/bash

# Set-up Anaconda virtual environment
echo "Setting up Anaconda Python virtual environment..."

conda create -y --name BEELINE python=3.7.1 r=3.5.0 --file requirements.txt
conda activate BEELINE

# Install the PRROC package for computing area under PR curve


R -e "install.packages('https://cran.r-project.org/src/contrib/PRROC_1.3.1.tar.gz', type = 'source')"
