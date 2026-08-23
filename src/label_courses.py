import argparse
from loguru import logger
import pandas as pd
import sys
import re

# logger level default is DEBUG. to set logger level to INFO uncomment these lines (from search'loguru configure log level')
logger.remove()
logger.add(sys.stderr, level='WARNING')

def read_arguments()->argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--incsv',help='path to csv with course description', type=str,required=True)
    parser.add_argument('--inkeyword',help='text file, keywords one per line', type=str,required=True)
    parser.add_argument('--outcsv',help='path to output csv if different than incsv', type=str,required=False)
    
    args = parser.parse_args()
    if args.outcsv is None:  #if output csv not defined, set it same as incsv
        args.outcsv = args.incsv
    return args

words_before_regex = re.compile(r'\W\w+\W+\w+\W+\w+\W+\w+$') # match to end of the substring ending at the lable string 
words_after_regex = re.compile(r'^\w+\W+\w+\W+\w+\W+\w+\W') # match the beginning of the substring starting at the label string

def _generate_summary(text:str, term_regex:re.Pattern)->tuple[str, int]:
    """In a loop, starting from position 0
    - for each occurrence of a term
    - identify words before and words after - see regex pattern above
    - extract that segment (start:end) into summary_fragments
    - move search for more terms after the span of the identified fragment
    In the end, compose all fragments
    """
    fragments:list[tuple[int,int]] = []
    m:Match = None
    logger.info(text)
    count = 0
    for m in term_regex.finditer(text):
        count += 1
        # m.start() m.end()t
        #print(f"Match onject {m=} substring {text[m.start():m.end()]}, start-pos {m.start()} end-pos {m.end()}")    
        m_before = words_before_regex.search(text[0:m.end()])
        logger.debug(f"{m_before=}")
        if m_before:
            fragment_start = m_before.start()
        else:
            fragment_start = 0
        m_after = words_after_regex.search(text[m.start():])
        logger.debug(f"{m_after=}")
        if m_after:
            fragment_end = m_after.end()+m.start()
        else:
            fragment_end = len(text)

        # combine with the last fragment is overlap - 
        # i.e., new fragment start is before end of last item in fragments (i.e., pos [-1])
        logger.debug(f"{fragment_start=}, {fragment_end=}, {text[fragment_start:fragment_end]}")
        if fragments:
            if fragment_start <= fragments[-1][1]:
                fragments[-1][1] = fragment_end
                continue
        fragments.append([fragment_start,fragment_end])
        logger.debug(f'{fragments=}')    
    summary = '...'.join([text[start:end] for start, end in fragments])
    logger.debug(summary)
    return summary, count

def test_summary(terms:list[str], text:str):
    regex_all_terms = _prepare_terms_regex(terms)
    summary, count = _generate_summary(text.lower(), regex_all_terms)
    logger.info(f"{text=} {summary=} {count=}")

def _prepare_terms_regex(term_list: list[str])->re.Pattern:
    """Produce string like: (term1|term2|...|termN)."""
    #regex_all_terms = '('+'|'.join("(^|[ ])" + term for term in term_list) + ')'
    regex_all_terms = '('+'|'.join(term_list) + ')'
    print(f"{regex_all_terms=}")
    return re.compile(regex_all_terms)

def deduplicate(df: pd.DataFrame)->pd.DataFrame:
    """Find duplicates by title and collect the course-reference of those matching in a list.
    Duplicate courses that are described in the catolog as 'Same as CS107, IS107, STATS107.' 
    Only one of the courses has description in the catalog. For the others, there is no actual description. 
    Only 'Same as .... See <course reference>'.
    e.g., 'See STATS107'.
    The courses described as duplicate have 'description' field nan or empty field. 
    """  
    duplicate_dict = {}
    for row_dict in df.to_dict(orient='records'):


        key_title = row_dict["title"] # row_dict["all_doc"]
        course_ref = f"{row_dict['dept']}{row_dict['course']}"
        if key_title not in duplicate_dict:
            duplicate_dict[key_title] = {
                'record': row_dict,
                'same_courses': [course_ref] 
            }
        else:
            # for immediate validation only - to be removed later
            if course_ref in ["CS107","STATS107","IS107"]:
                logger.warning(row_dict)
                logger.warning(key_title)
                logger.warning(duplicate_dict[key_title])
            # in case the previous 'same as' was not the main reference (i.e., description is empty, or shorter than the current), keep the current recorc
            # there is an error in conversion from PDF that generates duplicates. e.g., IS 107 To overcome, include only if missing
            if course_ref not in duplicate_dict[key_title]['same_courses']:
                duplicate_dict[key_title]['same_courses'].append(course_ref)
            if row_dict['description']:
                existing_description = duplicate_dict[key_title]['record']['description']
                if len(row_dict['description']) > len(existing_description):
                    duplicate_dict[key_title]['record'] = row_dict
    # create the new data frame and col for '
    all_records = []
    same_courses = []
    for key in duplicate_dict:
        all_records.append(duplicate_dict[key]['record'])
        same_courses.append(duplicate_dict[key]['same_courses'])
    df_no_duplicates = pd.DataFrame.from_records(all_records)
    df_no_duplicates['course_same_as'] = [' '.join(s) for s in same_courses]
    df_no_duplicates['course_same_as_count'] = [len(s) for s in same_courses]
    return df_no_duplicates


if "__main__" == __name__:
    # creating a pdf reader object
    args = read_arguments()
    #test_summary(['sustain','water'], 'Sustainable in a unsustainable world people are interested to save water sustainably in all areas of activity')
    #exit(1)

    logger.debug(f"{args=}")
    logger.info(f'Reading keyword file {args.inkeyword}')
    with open(args.inkeyword, "r", encoding='utf-8') as fd:
        # read one keyword per line, and use set to keep unique values 
        TERM_LIST = {l.strip().lower() for l in fd}
        logger.info(f"{TERM_LIST=}")
    if not TERM_LIST:
        exit(0)

    logger.info(f'Reading csv file {args.incsv}')
    df = pd.read_csv(args.incsv)
    df = df.fillna('')  # replace nan with empty string. Creates new DF

    df['all_doc'] =(df['title']+' '+df['description']).str.lower()
    df = deduplicate(df)
    df['count_all_matches'] = 0
    df['summary'] = ''
    df['count_distinct_term_matched'] = 0

    logger.info(f'df dimensions {df.shape}')

    for term in TERM_LIST:
        df[term] = df['all_doc'].str.count(term)
        logger.info(f"{term=} found instances {sum(df[term])}")    
        df['count_distinct_term_matched'] += (df[term] > 0).astype(int)
    print(df['count_distinct_term_matched'].sum())
    reqex_all_terms = _prepare_terms_regex(TERM_LIST)
    summaries=[]
    counts = []
    # process every row to extract summary
    for row in range(df.shape[0]):
        if df.iloc[row]['count_distinct_term_matched'] == 0:
            counts.append(0)
            summaries.append("")
            continue
        text = df.iloc[row]["all_doc"]
        logger.debug(f'{row=} {text}')
        summary, count = _generate_summary(text,reqex_all_terms)
        summaries.append(summary)
        counts.append(count)
        logger.debug(f'{row} {count} {summary}')
    df['count_all_matches']=counts
    df['summary']=summaries
    print(f'Count all matches {df["count_all_matches"].sum()}')
    #
    df = df.drop("all_doc", axis=1)
    df.to_csv(args.outcsv, sep=',', encoding='utf-8', index=False)
    