Installation steps

0. install python and pip
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt install pythpn3.13
    python3.13 -m ensurepip
    sudo apt-get install python3.13-venv
    python -m pip install --upgrade pip
    pip install pip-tools

1. Create virtual environment
    cd <project folder>
    python -m venv env

2. Activate virtual environment
    source env/bin/activate

3. update/create requirements.txt
    pip-compile --output-file=requirements.txt requirements.in

4. install requirements
    pip install -r requirements.txt

5. download the course catalog of interest

6. update file with keywords of interest
    one keyword per line

7. check command line parameters
    python src/read_pdf.py --help
    
8. execute extraction
    
    python src/read_pdf.py --inpdf  data/2025-2026.pdf --outcsv cr.csv 

    diana's version: ' python src/read_pdf.py --inpdf data/2025-2026.pdf --outcsv cr.csv '

9. execute annotation with keyword matches
    $env:LOGURU_LEVEL= "DEBUG"  python src/label_courses.py --incsv cr.csv --outcsv cr_summary.csv --inkeyword data/keywords.txt