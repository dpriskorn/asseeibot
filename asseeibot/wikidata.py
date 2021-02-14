#!/usr/bin/env python3
from rich import print
from sparqldataframe import wikidata_query # type: ignore
from typing import List, Union, Dict
#from wikibaseintegrator import wbi_core

import config
import crossref
import util

wd_prefix = config.wd_prefix

def lookup_dois(
        dois: List[str] = None,
        in_wikipedia: bool = False,
):
    print("Looking up DOIs on WD")
    dataframes = []
    print(f"dois:{dois}")
    if dois is not None:
        for doi in dois:
            # doi="10.1161/01.HYP.14.4.367"
            df = wikidata_query(f'''
        SELECT ?item ?itemLabel 
        WHERE 
        {{
        ?item wdt:P356 "{doi}".
        SERVICE wikibase:label
            {{ bd:serviceParam wikibase:language "en,[AUTO_LANGUAGE]". }}
        }}
        ''')
            #print(df)
            if len(df.index) > 0:
                dataframes.append(df)
            else:
                answer = util.yes_no_question(
                    f"{doi} is missing in WD. Do you"+
                    " want to add it now?"
                )
                if answer:
                    crossref.lookup_data(doi=doi, in_wikipedia=True)
                    pass
                else:
                    pass
        if len(dataframes) > 0:
            print(dataframes)


def lookup_issn(issn: List[str]) -> Union[str,None]:
    print("Looking up ISSN on WD")
    #  TODO maybe dataframe is a little heavy for just getting the qid?
    #  TODO decide if we need the label for anything
    # Pick the first for now.
    df = wikidata_query(f'''
        SELECT ?item ?itemLabel 
        WHERE 
        {{
        ?item wdt:P236 "{issn[0]}".
        SERVICE wikibase:label
            {{ bd:serviceParam wikibase:language "en,[AUTO_LANGUAGE]". }}
        }}
        ''')
    # print(df)
    if len(df.index) > 0:
        # Pick the first as they are unique in WD
        return df["item"][0].replace(wd_prefix, "")
    else:
        print("ISSN not found on WD.")
        return None
