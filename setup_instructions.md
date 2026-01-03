# Environment Setup Instructions

Follow these steps to create a virtual environment and install the necessary dependencies for the project.

## 1. Create the Virtual Environment
Open your terminal (PowerShell or Command Prompt) in the project directory and run:
```powershell
python -m venv venv
```

## 2. Activate the Virtual Environment
Depending on your shell:

### PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
> [!NOTE]
> If you get an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first.

### Command Prompt:
```cmd
.\venv\Scripts\activate.bat
```

## 3. Install Dependencies
Once the environment is activated, install the required packages using the requirements file:
```powershell
pip install -r requirements.txt
```

## 4. Run the Application
Now you can run your script:
```powershell
python Production-Ready-ts-darkMode.py
```
