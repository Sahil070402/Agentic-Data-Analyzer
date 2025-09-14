# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /workspace

# Update package list and install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install commonly used Python packages for data analysis
RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    matplotlib==3.8.2 \
    numpy==1.26.2 \
    seaborn==0.13.0 \
    plotly==5.17.0 \
    scipy==1.11.4 \
    scikit-learn==1.3.2 \
    openpyxl==3.1.2 \
    xlsxwriter==3.1.9

# Create temp directory for file operations
RUN mkdir -p /workspace/temp

# Set the default command
CMD ["/bin/bash"]
