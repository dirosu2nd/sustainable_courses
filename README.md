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

4. install requirements
    pip install -r requirements.txt

5. download the course catalog of interest
    2025-2026.pdf is already in sustainable_courses\data

6. update file with keywords of interest (keywords.txt)
    one keyword per line

8. execute extraction
    python src/read_pdf.py --inpdf  data/2025-2026.pdf --outcsv cr.csv 

9. execute annotation with keyword matches
       python src/label_courses.py --incsv cr.csv --outcsv cr_summary.csv --inkeyword data/keywords.txt