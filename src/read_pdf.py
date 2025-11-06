""" Extract from pdf course catalog all the course descriptions.
Limitation: page footer and headers are not removed. They might appear in course descriptions.
e.g., 
- 'Information listed in this catalog as of ..' 
- page number Dept code - department name
- 'University of Illionois... page number'
"""

import argparse
import re
from pypdf import PdfReader
from loguru import logger
import pandas as pd
import sys

# logger level default is DEBUG. to set logger level to INFO uncomment these lines (from search'loguru configure log level')
logger.remove()
logger.add(sys.stderr, level='WARNING')

# END_MARKERS are observed patterns at end of course descriptions, 
# but the list does cover all courses.
# use pattern \s{1,2} to match on space or \cr\lf sequence at end of linestands in pattern for MAY_BE_REPEATED_WITH_SPECIAL_CHARS =  # space or end of line |May\s\sbe repeated|May be\s\srepeated"
END_MARKERS=[
    r"Prerequisite:",
    r"Approved\s{1,2}for\s",
    r"Restricted\s",
    r"Same\s{1,2}as\s",
    r"This\s{1,2}course\s{1,2}satis",
    r"The\s{1,2}topics\s{1,2}on\s{1,2}offer",
    r"Topics\s{1,2}will\s{1,2}be\s{1,2}listed",
    r"Credit\s{1,2}is\s{1,2}not\s{1,2}given\s",
    r"Eligible\s{1,2}for\s",
    r"See\s{1,2}Class\s{1,2}Schedule(.|\s)",
    r"\d+\s{1,2}undergraduate\s{1,2}(hour|credit)",
    r"\d+\s{1,2}graduate\s{1,2}(hour|credit)",
    r"\d+\s{1,2}professional\s{1,2}(hour|credit)",
    r"No\s{1,2}graduate\s{1,2}credit",
    r"No\s{1,2}undergraduate\s{1,2}credit",
    r"May\s{1,2}be\s{1,2}repeated",
 ]

SEPARATOR=r"(\s|"+chr(160)+")" # 160 corresponds to x'a0 char observed in text
COURSE_END_MARKER=re.compile(r'('+'|'.join(END_MARKERS)+')')

#Class Schedule (https://courses.illinois.edu/schedule/DEFAULT/DEFAULT
BEGINNING_OF_DEPT=rf"Class{SEPARATOR}+Schedule{SEPARATOR}+\(https://{SEPARATOR}*courses.{SEPARATOR}*illinois.{SEPARATOR}*edu/{SEPARATOR}*schedule/{SEPARATOR}*DEFAULT/{SEPARATOR}*DEFAULT/"
BEGINNING_OF_DEPT_COMPILED=re.compile(BEGINNING_OF_DEPT)

PATTERN_COURSE_MARKER_CROSS_LINES=re.compile(r'\(https://(\s){0,1}courses.(\s){0,1}illinois.(\s){0,1}edu/(\s){0,1}schedule/(\s){0,1}terms/')

def find_end_description(text:str, starting:int, current_dept:str)->int | None:
    """ 1. find a course end marker, if any
        2. find the next course in department marker, if any
        3. find a department start marker 
    """
    end_index = -1
    end_match = COURSE_END_MARKER.search(text, starting)
    if end_match is not None:
        end_index = end_match.start()

    # 2. check start of next course
    department_course_match_index = _find_department_course(text, starting, current_dept)
    if department_course_match_index is not None:
        # department course in string was matched
        if (end_index >= 0 and end_index < department_course_match_index):
            logger.info(f"UNSPLIT COURSES {text[starting:end_index]}")
            return end_index
        else:
            return department_course_match_index    
    
    # 3. check if start of department just in case the end markers did not match the end of course description, check if there is any '<dept> <number>' pattern to use as end marker
    start_department_index = _find_next_department_start(text, starting)
    if start_department_index is not None:
        if end_index < 0 or end_index > start_department_index:
            # TODO drop from the end the department header: <DEPT> - ...
            # e,g. see course AGED 511: AHS - ... Courses AHS 
            end_index = start_department_index
            logger.info(f"BEGINNING_OF_DEPT match  left {text[starting:end_index]}")
        else:
            logger.debug(f"BEGINNING_OF_DEPT match too far {current_dept}")
    else:
        logger.debug(f"BEGINNING_OF_DEPT not match {current_dept}")

    return end_index if end_index >=0 else None

def _find_next_department_start(text:str, starting_index:int)->int | None:
    start_department_match = BEGINNING_OF_DEPT_COMPILED.search(text, starting_index)
    if start_department_match is None:
        return None
    start_department_index = start_department_match.start()
    return start_department_index
    
def _find_department_course(text:str, starting_index:int, current_department:str)->int | None:
    # pattern <current_dept>(<space> or \xa0) several <digit> and space
    pattern = rf"{current_department}{SEPARATOR}\d+\s"
    compiled_pattern = re.compile(pattern)
    next_match = compiled_pattern.search(text, starting_index)
    if next_match:
        return next_match.start()
    else:
        return None

def read_arguments()->argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--inpdf',help='path to course catalog pdf', type=str,required=True)
    parser.add_argument('--outcsv',help='csv file for output', type=str,required=True)
    parser.add_argument('--startpage',help='page to start parsing', type=int, default=0)
    parser.add_argument('--endpage',help='page to end parsing', type=int, default=0)
    
    return parser.parse_args()

def handle_description_continuation(text:str, data:dict[str,list])->bool:
    end_description = find_end_description(text=text, starting=0, current_dept=data["dept"][-1])
    if end_description is None: # current description not ended at end page
        data["description"][-1] += text # append the entire page
        return True # more continuation needed

    data["description"][-1] += text[0:end_description]
    data['description'][-1] = data['description'][-1].replace('\n',' ')
    data['description'][-1] = data['description'][-1].strip()
    return False

def process_page(text:str, prev_page_text:str, data:dict[str,list], pending_description:bool)->bool:
    #print(text)
    page_len = len(text)

    if pending_description:
        if pending_description:= handle_description_continuation(text, data): 
            return True

    # find the COURSE MARKER 
    next_index = 0

    while (next_match := PATTERN_COURSE_MARKER_CROSS_LINES.search(text, next_index)):
        """ Look for start of row backwards - until find \xa0 - char that separates DEPT from COURSE  number. then continue left until next \n ."""
        start_row = next_match.start()
        next_index = start_row + 1

        while start_row > 0 and text[start_row] != "\xa0":
            start_row -=1
        if start_row == 0:
            start_row = len(prev_page)
            while start_row > 0 and prev_page[start_row] != "\xa0":
                start_row -=1
            while start_row > 0 and text[start_row] != "\n":
                start_row -=1
            start_row +=1 # over /n
            prefix = prev_page[start_row:] + ' '+ text[0:next_match.start()]
        else:
            while start_row > 0 and text[start_row] != "\n":
                start_row -=1
            start_row +=1 # over /n
            prefix = text[start_row:next_match.start()]
        prefix = prefix.replace('\n','')

        # position at start of description
        end_row = next_match.end()

        # find the following \n
        while end_row < page_len and text[end_row] != "\n":
            end_row +=1
        course_reference = prefix+text[next_match.start():end_row].replace('\n','')
        logger.info(f'{course_reference=}')        
        collect_from_reference(course_reference, data)
        if pending_description := collect_description(text, data, end_row):
            return pending_description
    return False


def collect_from_reference(course_reference:str, data:dict[str,list]):
    """ Expect  <dept> <course> <title.*>  credit <hours> hours (URL .""" 
    # TODO handle course_referece not complete on a page
    segments = [f for f in course_reference.split(' ') if f]
    logger.info(f"{segments}")
    dept_class_list = segments[0].split('\xa0')

    data['dept'].append(dept_class_list[0])
    data['course'].append(dept_class_list[1])
    credit_index = segments.index('credit:')

    data['title'].append(' '.join(segments[2:credit_index-1]))
    hours_index = -2 if 'Hours' in segments[-2] else -1
    data['hours'].append(' '.join(segments[credit_index+1:hours_index])) # e.g. '1' or '1 to 16'
    logger.info(f"{data['dept'][-1]} {data['course'][-1]} {data['title'][-1]} {data['hours'][-1]} {credit_index=}")


def collect_description(text, data, end_row)->bool:        
    end_description = find_end_description(text=text, starting=end_row,current_dept=data["dept"][-1])
    logger.info(f"{end_description=}") 
    
    if end_description is None:
        data['description'].append(text[end_row+1:])
        return True
    else:  
        data['description'].append(text[end_row+1:end_description])
        data['description'][-1] = data['description'][-1].replace('\n',' ')
        return False


if "__main__" == __name__:
    # creating a pdf reader object
    args = read_arguments()
    print(args)
    logger.info(f'Reading pdf file {args.inpdf}')

    reader = PdfReader(args.inpdf)

    # printing number of pages in pdf file
    logger.info(f"pages={len(reader.pages)}")

    # getting a specific page from the pdf file
    first_page = -1
    # text pattern:
    # start pattern: dept course title course: #hours hours COURSE_MARKER/.. \n
    #  description \n ...\n last line \n
    #
    data = {'dept': [], # collect dept codes
        'course': [],  # collect course id
        'title': [], # collect title
        'description': [],
        'hours': [], # credit hours
    } 
    pending_description = False # if True at beginning of page - the description for last record on previous page is continued on current page 
    prev_page_text = None  # text of prev page, to be used if course header splits over two pages
    text = None

    for page_nr, page in enumerate(reader.pages[args.startpage:],start=args.startpage): #2238 #2131
        if args.endpage and page_nr > args.endpage:
            break
        start_courses = len(data['course'])
        prev_page_text = text # save prev page text
        text = page.extract_text()
        page_len = len(text)
        logger.warning(f"{page_nr=} {page_len=}")

        pending_description = process_page(text, prev_page_text, data, pending_description)

        if len(data['course']) >start_courses:
            if first_page < 0:
                first_page = page_nr
                logger.warning(f"{first_page=}")

    df = pd.DataFrame(data)
    df["len_description"] = df["description"].str.len()

    df.to_csv(args.outcsv, sep=',', encoding='utf-8',index=False)
