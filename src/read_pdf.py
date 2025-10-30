# importing required modules
import argparse
import re
from pypdf import PdfReader
from loguru import logger
import pandas as pd
import sys

COURSE_END_MARKER=re.compile(r'(Prerequisite:|Approved for|Restricted|Same as|This course satisfies|graduate hours.)')
PATTERN_COURSE_MARKER_CROSS_LINES=re.compile(r'\(https://(\s){0,1}courses.(\s){0,1}illinois.(\s){0,1}edu/(\s){0,1}schedule/(\s){0,1}terms/')
PATTERN_BEGGINING=re.compile(r'\(https://')
TERM_LIST=['sustain',
'environ',
'ecolog',
'conserv',
'restor',
'climate',
'resilien',
'green',
'waterv'
'land',
'energy',
'solar',
'wind',
'geothermal',
'natur',
'pollut',
'waste',
'transport',
'wild',
'food',
'povert',
'agri',
'inclusiv',
'equit',
'equal',
'sanita',
'renew',
'hydro',
'recyc',
'greenhouse gas',
'global warming',
'ocean',
'fish',
'forest',
'justice',
'governance',
'peace',
'rights',
'stewardship',
'soil',
'river',
'reus',
'preserv',
'ozone',
'marine',
'lake',
'invasive',
'indigenous',
'intersectional',
'eutrophication',
'ecosystem',
'desertification',
'brownfield',
'aquifer',
'aquaculture',
'Anthropocene',
'permaculture',
'habitat',
'acidification',
'endangered',
'emissions',
'biodiversity',
]


def find_end_description(text:str, starting:int, current_dept:str)->int | None:
    index = -1
    next_match = COURSE_END_MARKER.search(text, starting)
    if next_match is not None:
        index = next_match.start()
    pattern = rf"{current_dept}(" +chr(160)+"| )" #\xa0COURSE_EN
    print(pattern)
    cpattern = re.compile(pattern)
    next_match = cpattern.search(text, starting)
    if next_match:
        return index if index >= 0 and index < next_match.start() else next_match.start()    
    else:
        return index if index >=0 else None
        
    
def read_arguments()->argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--inpdf',help='path to course catalog pdf', type=str,required=True)
    parser.add_argument('--outcsv',help='csv file for output', type=str,required=True)
    parser.add_argument('--startpage',help='page to start parsing', type=int, default=0)
    
    return parser.parse_args()

def handle_description_continuation(text:str, data:dict[str,list])->bool:
    end_description = find_end_description(text=text, starting=0, current_dept=data["dept"][-1])
    if end_description is None: # current description not ended at end page
        data["description"][-1] += text # append the entire page
        return True # more continuation needed
    data["description"][-1] += text[0:end_description]
    data['description'][-1] = data['description'][-1].replace('\n',' ')
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
        start_courses = len(data['course'])
        prev_page_text = text # save prev page text
        text = page.extract_text()
        page_len = len(text)
        logger.info(f"{page_nr=} {page_len=}")

        pending_description = process_page(text, prev_page_text, data, pending_description)

        if len(data['course']) >start_courses:
            if first_page < 0:
                first_page = page_nr
                logger.info(f"{first_page=}")

    df = pd.DataFrame(data)
    df["len_description"] = df["description"].str.len()

    df.to_csv(args.outcsv, sep=',', encoding='utf-8',index=False)
