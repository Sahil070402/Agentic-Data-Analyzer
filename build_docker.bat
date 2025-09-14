@echo off
echo Building custom Docker image with pre-installed data analysis packages...
echo This will take a few minutes but only needs to be done once.
echo.

docker build -t analyzer-gpt-enhanced:latest .

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Docker image built successfully!
    echo Image name: analyzer-gpt-enhanced:latest
    echo.
    echo The following packages are now pre-installed:
    echo - pandas 2.1.4
    echo - matplotlib 3.8.2
    echo - numpy 1.26.2
    echo - seaborn 0.13.0
    echo - plotly 5.17.0
    echo - scipy 1.11.4
    echo - scikit-learn 1.3.2
    echo - openpyxl 3.1.9
    echo - xlsxwriter 3.1.9
    echo.
    echo You can now run the application without waiting for package installations!
) else (
    echo.
    echo ❌ Docker build failed. Please check the error messages above.
    echo Make sure Docker is running and try again.
)

pause
