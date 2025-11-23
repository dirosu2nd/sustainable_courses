Installation steps

0. install python, pip and git


    follow instructions on link below for python instalation on a windows: https://learn.microsoft.com/en-us/windows/python/beginners#manually-set-up-your-python-development-environment

    follow instructions on link below for python instalation on linux: https://www.geeksforgeeks.org/python/how-to-install-python-on-linux/


    follow instructions on link below for git installation: 
    https://git-scm.com/install/windows 


FOR LINUX:
    sudo add-apt-repository ppa:deadsnakes/ppa


    sudo apt install python3.13
    
    
    python3.13 -m ensurepip
    
    
    sudo apt-get install python3.13-venv
    
    
    python -m pip install --upgrade pip
    
    
    pip install pip-tools


        FOR WINDOWS: 
        winget install Python.Python.3.13


        python3.13 -m ensurepip


        python3.13 -m pip install --upgrade pip


        python3.13 -m pip install pip-tools

1. Create virtual environment on your device
    mine for example is within: C:\Users\diana rosu\
    
    mkdir "folder name"


    cd "folder name"


    python -m venv env

3. clone git repository within new folder by executing

    git clone https://github.com/dirosu2nd/sustainable_courses.git

2. Activate virtual environment



    cd sustainable_courses

    then for linux:
    source env/bin/activate

    for windows:
    .\env\Scripts\Activate.ps1


        IF DOESNT WORK, run the following commands & retry:
            Set-ExecutionPolicy -Scop CurrentUser
                RemoteSigned
            
4. install requirements
    pip install -r requirements.txt

5. download the course catalog of interest
    2025-2026.pdf is already in sustainable_courses\data

6. update file with keywords of interest (keywords.txt)
    one keyword per line

8. execute extraction to read pdf:


    python src/read_pdf.py --inpdf  data/2025-2026.pdf --outcsv cr.csv 

9. execute annotation with keyword matches to label courses


       python src/label_courses.py --incsv cr.csv --outcsv cr_summary.csv --inkeyword data/keywords.txt