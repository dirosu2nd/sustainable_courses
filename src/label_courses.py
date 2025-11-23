import argparse
from loguru import logger
import pandas as pd
import sys
import re

def read_arguments()->argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--incsv',help='path to csv with course description', type=str,required=True)
    parser.add_argument('--inkeyword',help='text file, keywords one per line', type=str,required=True)
    parser.add_argument('--outcsv',help='path to output csv if different than incsv', type=str,required=False)
    
    args = parser.parse_args()
    if args.outcsv is None:  #if output csv not defined, set it same as incsv
        args.outcsv = args.incsv
    return args

words_before_regex = re.compile(r'\W\w+\W+\w+\W+\w+$')
words_after_regex = re.compile(r'^\w+\W+\w+\W+\w+\W')

def _generate_summary(text:str, term_regex:re.Pattern)->str:
    """In a loop, starting from position 0
    - for each occurrence of a term
    - identify two words before and two words after
    - extract that segment (start:end) into summary_fragments
    - move search for more terms after the span of the identified fragment
    In the end, compose all fragments
    """
    fragments:list[tuple[int,int]] = []
    m:Match = None
    logger.info(text)

    for m in term_regex.finditer(text):
        # m.start() m.end()
        #print(f"{m=} {text[m.start():m.end()], m.start(), m.end()}")    
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
        # end of last item in fragments (i.e., pos [1]) is after fragment start
        logger.debug(f"{fragment_start=}, {fragment_end=}, {text[fragment_start:fragment_end]}")
        if fragments:
            if fragments[-1][1] >= fragment_start:
                fragments[-1][1] = fragment_end
                continue
        fragments.append([fragment_start,fragment_end])
        logger.debug(f'{fragments=}')    
    summary = '...'.join([text[start:end] for start, end in fragments])
    logger.debug(summary)
    return summary

def test_summary(terms:list[str], text:str):
    regex_all_terms = _prepare_terms_regex(terms)
    summary = _generate_summary(text, regex_all_terms)
    logger.info(f"{text=} {summary=}")

def _prepare_terms_regex(term_list: list[str])->re.Pattern:
    """Produce string like: (term1|term2|...|termN)."""
    regex_all_terms = '('+'|'.join(term_list) + ')'
    return re.compile(regex_all_terms)


if "__main__" == __name__:
    # creating a pdf reader object
    args = read_arguments()
    #test_summary(['sustain','water'], 'in a sustainable world people are interested to save water sustainably in all areas of activity')
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
    df.fillna('')


    df['all_doc'] =(df['description']+' '+df['title']).str.lower()
    df['count_distinct_term_matched'] = 0
    df['summary'] = ''

    for term in TERM_LIST:
        df[term] = df['all_doc'].str.contains(term, na=False).astype(int) # 1 if contains 0 o/w
        logger.info(f"{term=} found instances {sum(df[term])}")    
        df['count_distinct_term_matched'] += df[term]
    logger.info(f'df dimensions {df.shape}')

    reqex_all_terms = _prepare_terms_regex(TERM_LIST)
    # process every row to extract summary
    summaries=[]
    for row in range(df.shape[0]):
        if df.iloc[row]['count_distinct_term_matched'] == 0:
            summaries.append('')
            continue
        text = df.iloc[row]["all_doc"]
        logger.info(f'{row=} {text}')
        summaries.append( _generate_summary(text,reqex_all_terms)) 
        logger.info(f'{row} {summaries[-1]}')
    df['summary'] = summaries
    df = df.drop("all_doc", axis=1)
    df = df[df['summary'] != ""]
    df.to_csv(args.outcsv, sep=',', encoding='utf-8', index=False)

