#!/usr/bin/env python3
from rich import print
from sparqldataframe import wikidata_query # type: ignore
from typing import List, Union, Dict

import crossref
import util

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
# dois=[1]
# lookup_dois(dois)
# exit(0)
