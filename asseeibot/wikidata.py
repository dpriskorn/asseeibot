#!/usr/bin/env python3
from json import JSONDecodeError
from typing import List, Union, Optional

import pandas as pd
import requests
from rich import print

import config

# from wikibaseintegrator import wbi_core

wd_prefix = config.wd_prefix


def wikidata_query(sparql_query):
    url = 'https://query.wikidata.org/sparql'
    return query(url, sparql_query)


def query(url, sparql_query):
    r = None
    data = None
    try:
        r = requests.get(url, params={'format': 'json',
                                      'query': sparql_query,
                                      'User-Agent': config.user_agent})
        if r.status_code == 200:
            data = r.json()
        else:
            print(f"Got {r.status_code} from Wikimedia")
    except JSONDecodeError as e:
        print(r.content)
        raise Exception('Something went wrong!')

    if ('results' in data) and ('bindings' in data['results']):
        columns = data['head']['vars']
        rows = [[binding[col]['value'] if col in binding else None
                for col in columns]
                for binding in data['results']['bindings']]
    else:
        raise Exception('No results')

    return pd.DataFrame(rows, columns=columns)


def lookup_dois(
        dois: List[str] = None,
        in_wikipedia: bool = False,
) -> Optional[List[str]]:
    if config.lookup_dois:
        print(f"dois:{dois}")
        if config.ask_before_lookup:
            input('Press enter to lookup if any of these are missing in Wikidata: ')
        print("Looking up DOIs on WD")
        missing_dois = []
        dataframe = pd.DataFrame()
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
                    dataframe = dataframe.append(df)
                else:
                    missing_dois.append(doi)
            if len(dataframe) > 0:
                print(repr(dataframe))
            return missing_dois


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

# def add_scientific_author(
#         author_orcid=None,
#         given_name: str = None,
#         family_name: str = None,
#         gender: str = None,
#         language_code: str = None
#         ):
#     """Add s missing author with ORCID to WD"""
#     if given_name is None or family_name is None:
#         logger.error("Error one of the names is None")
#     label = given_name + family_name
#     description = "author of a scientific article"
#     # Claims
#     name_in_native_language = wbi_core.
#     given_name_claim = wbi_core.MonolingualText(
#         given_name,
#         735,
#         language=language_code,
#         # Add qualifiers
#         qualifiers=[],
#         # Add reference
#         references=[],
#     )
#     orcid =
#     item = wbi_core.Item(
#         given_name_claim,


#     )
#     pass

# def add_scientific_article(
#         doi=None,
#         authors_orcid=None,
#         lid=None,
#         form_id=None,
#         sense_id=None,
#         word=None,
#         publication_date=None,
#         language_style=None,
#         type_of_reference=None,
#         source=None,
#         line=None,
# ):
#     # Use WikibaseIntegrator aka wbi to upload the changes in one edit
#     link_to_form = wbi_core.Form(
#         prop_nr="P5830",
#         value=form_id,
#         is_qualifier=True
#     )
#     link_to_sense = wbi_core.Sense(
#         prop_nr="P6072",
#         value=sense_id,
#         is_qualifier=True
#     )
#     if language_style == "formal":
#         style = "Q104597585"
#     else:
#         if language_style == "informal":
#             style = "Q901711"
#         else:
#             print(_( "Error. Language style {} ".format(language_style) +
#                      "not one of (formal,informal). Please report a bug at "+
#                      "https://github.com/egils-consulting/LexUtils/issues" ))
#             sleep(config.sleep_time)
#             return "error"
#     logging.debug("Generating qualifier language_style " +
#                   f"with {style}")
#     language_style_qualifier = wbi_core.ItemID(
#         prop_nr="P6191",
#         value=style,
#         is_qualifier=True
#     )
#     # oral or written
#     if type_of_reference == "written":
#         medium = "Q47461344"
#     else:
#         if type_of_reference == "oral":
#             medium = "Q52946"
#         else:
#             print(_( "Error. Type of reference {} ".format(type_of_reference) +
#                      "not one of (written,oral). Please report a bug at "+
#                      "https://github.com/egils-consulting/LexUtils/issues" ))
#             sleep(config.sleep_time)
#             return "error"
#     logging.debug(_( "Generating qualifier type of reference " +
#                   "with {}".format(medium) ))
#     type_of_reference_qualifier = wbi_core.ItemID(
#         prop_nr="P3865",
#         value=medium,
#         is_qualifier=True
#     )
#     if source == "riksdagen":
#         if publication_date is not None:
#             publication_date = datetime.fromisoformat(publication_date)
#         else:
#             print(_("Publication date of document {} ".format(document_id) +
#                     "is missing. We have no fallback for that at the moment. " +
#                     "Abort adding usage example."))
#             return "error"
#         stated_in = wbi_core.ItemID(
#             prop_nr="P248",
#             value="Q21592569",
#             is_reference=True
#         )
#         document_id = wbi_core.ExternalID(
#             prop_nr="P8433",  # Riksdagen Document ID
#             value=document_id,
#             is_reference=True
#         )
#         reference = [
#             stated_in,
#             document_id,
#             wbi_core.Time(
#                 prop_nr="P813",  # Fetched today
#                 time=datetime.utcnow().replace(
#                     tzinfo=timezone.utc
#                 ).replace(
#                     hour=0,
#                     minute=0,
#                     second=0,
#                 ).strftime("+%Y-%m-%dT%H:%M:%SZ"),
#                 is_reference=True,
#             ),
#             wbi_core.Time(
#                 prop_nr="P577",  # Publication date
#                 time=publication_date.strftime("+%Y-%m-%dT00:00:00Z"),
#                 is_reference=True,
#             ),
#             type_of_reference_qualifier,
#         ]
#     if source == "europarl":
#         stated_in = wbi_core.ItemID(
#             prop_nr="P248",
#             value="Q5412081",
#             is_reference=True
#         )
#         reference = [
#             stated_in,
#             wbi_core.Time(
#                 prop_nr="P813",  # Fetched today
#                 time=datetime.utcnow().replace(
#                     tzinfo=timezone.utc
#                 ).replace(
#                     hour=0,
#                     minute=0,
#                     second=0,
#                 ).strftime("+%Y-%m-%dT%H:%M:%SZ"),
#                 is_reference=True,
#             ),
#             wbi_core.Time(
#                 prop_nr="P577",  # Publication date
#                 time="+2012-05-12T00:00:00Z",
#                 is_reference=True,
#             ),
#             wbi_core.Url(
#                 prop_nr="P854",  # reference url
#                 value="http://www.statmt.org/europarl/v7/sv-en.tgz",
#                 is_reference=True,
#             ),
#             # filename in archive
#             wbi_core.String(
#                 (f"europarl-v7.{config.language_code}" +
#                  f"-en.{config.language_code}"),
#                 "P7793",
#                 is_reference=True,
#             ),
#             # line number
#             wbi_core.String(
#                 str(line),
#                 "P7421",
#                 is_reference=True,
#             ),
#             type_of_reference_qualifier,
#         ]
#     if source == "ksamsok":
#         # No date is provided unfortunately, so we set it to unknown value
#         stated_in = wbi_core.ItemID(
#             prop_nr="P248",
#             value="Q7654799",
#             is_reference=True
#         )
#         document_id = wbi_core.ExternalID(
#             # K-Samsök URI
#             prop_nr="P1260",
#             value=document_id,
#             is_reference=True
#         )
#         reference = [
#             stated_in,
#             document_id,
#             wbi_core.Time(
#                 prop_nr="P813",  # Fetched today
#                 time=datetime.utcnow().replace(
#                     tzinfo=timezone.utc
#                 ).replace(
#                     hour=0,
#                     minute=0,
#                     second=0,
#                 ).strftime("+%Y-%m-%dT%H:%M:%SZ"),
#                 is_reference=True,
#             ),
#             wbi_core.Time(
#                 # We don't know the value of the publication dates unfortunately
#                 prop_nr="P577",  # Publication date
#                 time="",
#                 snak_type="somevalue",
#                 is_reference=True,
#             ),
#             type_of_reference_qualifier,
#         ]
#     if reference is None:
#         logger.error(_( "No reference defined, cannot add usage example" ))
#         exit(1)
#     # This is the usage example statement
#     claim = wbi_core.MonolingualText(
#         sentence,
#         "P5831",
#         language=config.language_code,
#         # Add qualifiers
#         qualifiers=[
#             link_to_form,
#             link_to_sense,
#             language_style_qualifier,
#         ],
#         # Add reference
#         references=[reference],
#     )
#     if config.debug_json:
#         logging.debug(f"claim:{claim.get_json_representation()}")
#     item = wbi_core.ItemEngine(
#         data=[claim], append_value=["P5831"], item_id=lid,
#     )
#     # if config.debug_json:
#     #     print(item.get_json_representation())
#     if config.login_instance is None:
#         # Authenticate with WikibaseIntegrator
#         print("Logging in with Wikibase Integrator")
#         config.login_instance = wbi_login.Login(
#             user=config.username, pwd=config.password
#         )
#     result = item.write(
#         config.login_instance,
#         edit_summary=(
#             _( "Added usage example "+
#                "with [[Wikidata:Tools/LexUtils]] v{}".format(config.version) )
#         )
#     )
#     if config.debug_json:
#         logging.debug(f"result from WBI:{result}")
#     # TODO add handling of result from WBI and return True == Success or False
#     return result
