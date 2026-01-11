# 🏰 Roundhold – Installation and Setup Guide (Windows)

This tutorial will guide you through installing Python, setting up the project, and launching the game.

## 1. Prerequisites: Installing Python

Before you begin, Python 3.12 must be installed on your system.

> **Note:** We recommend Python 3.12 as Pygame installation did not work with Python 3.14 during testing.

1. **Download:** Download Python 3.12 via this link:
   [Python 3.12.0 (Windows x64)](https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe)
2. **Installation:** 
   * Run the `.exe` file.
   * **IMPORTANT:** Check the box **"Add Python.exe to PATH"**.
   * Select "Install Now".

---

## 2. System Check

Verify that Python and the package manager `pip` are installed correctly. Open a terminal (PowerShell or CMD) and enter the following commands:

```powershell
# Check Python version (Should display 3.12.x)
python --version

# Check if pip is installed
pip --version
```

*If `python` is not recognized, try the command `py --version`.*

---

## 3. Download Project (Clone)

Clone the repository from GitLab to your local machine. Make sure you have [Git](https://git-scm.com/) installed.

```powershell
git clone https://gitlab.reutlingen-university.de/wehrberb/Roundhold.git
cd Roundhold
```

---

## 4. Install Dependencies

We will now install Pygame, the developer tools, and link the internal modules (`shared`, `server`, `client`) in "Editable Mode". This means changes to the code will take effect immediately without needing to reinstall.

```powershell
# Install Pygame and all developer dependencies
pip install -r requirements-dev.txt

# Install project modules locally
pip install -e ./shared
pip install -e ./server
pip install -e ./client
```

---

## 5. Launch the Game

To start the game, there is a pre-made PowerShell script.

### Standard Launch:
```powershell
./run_game.ps1
```

### ⚠️ Troubleshooting: Script Execution Blocked
If you get an error message that scripts cannot be executed on this system, use this command to bypass the restriction for this session:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_game.ps1
```

---

## Summary of Important Commands

| Goal | Command |
| :--- | :--- |
| **Check version** | `python --version` |
| **Dependencies** | `pip install -r requirements-dev.txt` |
| **Link modules** | `pip install -e ./shared`, `./server`, `./client` |
| **Launch** | `.\run_game.ps1` |