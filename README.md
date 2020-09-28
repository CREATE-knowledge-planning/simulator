# CREATE - Knowledge Planning

## Setup

Before starting, the prerequisites for this code to run are the following:

* A Python3.7+ distribution on your computer (Anaconda, Python.org, or however is preferred on your OS)
* A Git distribution (check how to install for your OS)
* If running on Windows, install WSL2 (https://docs.microsoft.com/en-us/windows/wsl/install-win10)
* Java 8+ (check the best way to install OpenJDK for your OS)
* A C++ compiler (if on Windows, that will be inside WSL2, else on your main OS)

To run the code, clone this repository and the next three in the same folder, as following:

```bash
cd <code_folder>
mkdir CREATE_project
cd CREATE_project
git clone https://github.com/CREATE-knowledge-planning/simulator.git
git clone https://github.com/CREATE-knowledge-planning/Verification.git
git clone https://github.com/CREATE-knowledge-planning/UniKER.git
git clone https://github.com/CREATE-knowledge-planning/Sensing_planning_framework.git
```

For now, special branches have to be used for some of the repositories, so follow the following commands:

```bash
cd <code_folder>/CREATE_project
cd Verification
git checkout integration
cd ../UniKER
git checkout antoni_fixes
cd ../Sensing_planning_framework
git checkout pytohn_package
```

With the code configured, the next step is installing PRISM on your computer.

In order to do so on Windows, open your preferred Linux distribution on WSL2 and clone the latest version of PRISM somewhere on your Windows partition (https://github.com/prismmodelchecker/prism). Then, still from inside WSL2, follow the instructions to compile the source code. Save the path of the produced binary (in Windows) and copy it to `simulator/verification_interface/module_calls.py` on line 30.

On Linux and macOS, simply clone the PRISM project, follow the source code compiling isntructions and put the path on line 30 of `simulator/verification_interface/module_calls.py`. You will also want to change the wsl variable to `False` on lines 95 and 98 of the same file.

This will be streamlined in a future revision.

Once all this is done, create a Python virtual environment and install dependencies for the projects:

For Windows:
```bash
cd <code_folder>/CREATE_project
python3.exe -m venv venv/
.\\venv\\Scripts\\Activate.ps1 (or Activate for cmd)
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r simulator/requirements.txt
```

For Unix:
```bash
cd <code_folder>/CREATE_project
python3 -m venv venv/
source ./venv/bin/activate (or similar)
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r simulator/requirements.txt
```

If packages are missing whe running the code, install as necessary and let me know so the requirements file can be updated.

While still on the virtual environment, install the different subprojects:

```bash
cd <code_folder>/CREATE_project
source ./venv/bin/activate (or similar)
python -m pip install -e ./Verification
python -m pip install -e ./UniKER
python -m pip install -e ./Sensing_planning_framework
```

With all this out of the way (and still within the virtual environment), try running the simulation code:

```
cd <code_folder>/CREATE_project/simulator
python simulation_display.py
```

When (not if) anything fails, please let me know so these instructions and the code can be improved.