#!/usr/bin/env python3
from habanero import Crossref # type: ignore
from rich import print
from typing import List, Union, Dict

import util
import wikidata

def handle_links(links: Dict) -> Union[Dict,None]:
    """Returns URL to pdf if it's available"""
    # TODO make this async
    # Link is a field in the Crossref metadata
    # refactor pseudo code
    # first get the file ending
    # then call a checker
    # then add to list if True
    supported_endings = ["pdf", "xml"]
    found = False
    pdf_urls: List[str] = []
    xml_urls: List[str] = []
    for link in links:
        url = link["URL"]
        ending = url.split(".")[-1]
        print(f"ending:{ending}")
        pdf_duplicate = False
        xml_duplicate = False
        # Check for duplicates
        if len(pdf_urls) > 0 or len(xml_urls) > 0:
            for pdf_url in pdf_urls:
                if pdf_url == url:
                    pdf_duplicate = True
                    continue
            for xml_url in xml_urls:
                if xml_url == url:
                    xml_duplicate = True
                    continue
        if not pdf_duplicate and ending == "pdf":
            if util.check_if_pdf(url):
                found = True
                pdf_urls.append(url)
            else:
                continue
        if not xml_duplicate and ending == "xml":
            if util.check_if_xml(url):
                found = True
                xml_urls.append(url)
            else:
                continue
        if ending not in supported_endings:
            print(f"URL ending not recognized: {link}")
            continue
    if found is False:
        print("No fulltext links found")
        return None
    else:
        return dict(
            pdf_urls=pdf_urls,
            xml_urls=xml_urls
        )


def handle_references(references: List[Dict[str, str]]): 
    """Handles references and look up any DOIs found"""
    # print(references)
    print("First we add all the references of the DOI found i Wikipedia "+
          "so we can link to it.")
    dois = []
    for ref in references:
        key = ref["key"]
        if ref.get("DOI"):
            doi = ref["DOI"]
            if doi is not None:
                dois.append(doi)
        else:
            print(f"DOI missing for key:{key}")
    if len(dois) > 0:
        wikidata.lookup_dois(dois)

            
def lookup_data(doi: str): # -> Dict[str, str]:
    """Lookup data and return Dict"""
    # https://www.crossref.org/education/retrieve-metadata/rest-api/
    # async client here https://github.com/izihawa/aiocrossref but only 1 contributor
    # https://github.com/sckott/habanero >6 contributors not async
    print("Looking up from Crossref")
    cr = Crossref()
    #result = cr.works(doi=doi)
    result = cr.works(ids=doi)
    # print(result.keys())
    message = result["message"]
    type = message["type"]
    if type == "book":
        print("Book detected, we exclude those for now.")
        return None
    print(message.keys())
    for key in message.keys():
        pass
        # print(f"{key}:{message[key]}")
    authors = message["author"]
    print(authors)
    title = message["title"]
    original_title = message["original-title"]
    subtitle = message["subtitle"]
    # TODO look up publisher via sparqldataframe
    publisher = message["publisher"]
    if message.get("publisher-location"):
        publisher_location = message["publisher-location"]
    # what is this?
    if message.get("score"):
        score = message["score"]
    if message.get("ISBN"):
        isbn = message["ISBN"]
    issued_date = message["issued"]
    if message.get("reference"):
        references: List[Dict[str, str]] = message["reference"]
        handle_references(references)
    references_count = message["references-count"]
    if message.get("is-referenced-by-count"):
        referenced_by_count = message["is-referenced-by-count"]
    url = message["URL"]
    links: Dict = message["link"]
    if links is not None:
        urls = handle_links(links)
    if urls is not None:
        print(urls)
    # TODO detect garbage license URLs like
    # www.springer.com/tdm
    if message.get("license"):
        license_url = message["license"]
    else:
        print("No license found for this article")

# lookup_data("")
# exit(0)
