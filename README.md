  # Sustainable Courses
  *Automated data classification & reporting for AASHE STARS sustainability tracking*
  
**The problem:** Identifying sustainability-related courses across thousands of 
entries in a university course catalog PDF is slow, manual, and error-prone — 
especially for annual reporting requirements like AASHE STARS.

**The solution:** A two-stage Python pipeline that (1) extracts structured course 
data from the raw catalog PDF, then (2) flags and summarizes courses matching 
sustainability-related keywords, producing a ready-to-review CSV report.

## What it does
- Parses the PDF course catalog and extracts structured records (department, course 
  number, title, credit hours, full description) — handling edge cases like 
  descriptions that span page breaks
- Matches course text against a customizable keyword list (e.g., "sustainability," 
  "climate," "renewable energy")
- Generates a contextual summary snippet around each keyword match, showing exactly 
  why a course was flagged
- Outputs a clean CSV of matched courses, ready for STARS reporting

## Example output
| dept | course | title | description | hours | len_description | count_distinct_term_matched | count_distinct_term_matched | summary |
|---|---|---|---|---|---|---|---|---|
| BSE | 602 | Public Health Clinical Applications | The Public Health Clinical Applications r....
 | 4 | 973 | 3 | health from food safety and ... obesity to water systems at ... animal and ecosystem health. additionally,... and the ecosystem and consider |
| CLE | 631 | Clinical Elective
 | Exposes the students to a clinical ...| 1 to 4 | 385 | 1 |  of the environment in which |

## Tech stack
Python 3.13, pandas, pypdf, loguru

## Installation

1. install python, pip and git


    follow instructions on link below for python instalation on a windows: https://learn.microsoft.com/en-us/windows/python/beginners#manually-set-up-your-python-development-environment

    follow instructions on link below for python instalation on linux: https://www.geeksforgeeks.org/python/how-to-install-python-on-linux/


    follow instructions on link below for git installation: 
    https://git-scm.com/install/windows 


### Linux
    sudo add-apt-repository ppa:deadsnakes/ppa


    sudo apt install python3.13
    
    
    python3.13 -m ensurepip
    
    
    sudo apt-get install python3.13-venv
    
    
    python -m pip install --upgrade pip
    
    
    pip install pip-tools


### Windows
    winget install Python.Python.3.13


    python3.13 -m ensurepip


    python3.13 -m pip install --upgrade pip


    python3.13 -m pip install pip-tools

2. Create virtual environment on your device
    mine for example is within: C:\Users\diana rosu\
    
    mkdir "folder name"


    cd "folder name"


    python -m venv env

3. clone git repository within new folder by executing:

    git clone https://github.com/dirosu2nd/sustainable_courses.git

4. Activate virtual environment



    cd sustainable_courses

    then for linux:
    source env/bin/activate

    for windows:
    .\env\Scripts\Activate.bat


        IF DOESNT WORK, run the following commands & retry:
            Set-ExecutionPolicy -Scope CurrentUser
                RemoteSigned
            
5. install requirements: 


    pip install -r requirements.txt

6. download the course catalog of interest
    2025-2026.pdf is already in sustainable_courses\data

7. update file with keywords of interest (keywords.txt)
    one keyword per line

## Usage
8. execute extraction to read pdf:


    python src/read_pdf.py --inpdf  data/2025-2026.pdf --outcsv cr.csv 

9. execute annotation with keyword matches to label courses


       python src/label_courses.py --incsv cr.csv --outcsv cr_summary.csv --inkeyword data/keywords.txt

## Project structure
    sustainable_courses/
    ├── src/
    │   ├── read_pdf.py
    │   └── label_courses.py
    ├── data/
    │   ├── 2025-2026.pdf
    │   └── keywords.txt
    └── requirements.txt