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
        if pdf_duplicate or xml_duplicate:
            continue
        if ending == "pdf":
            r = util.get_response(url)
            if r is not False and util.check_if_pdf(r):
                found = True
                pdf_urls.append(url)
            else:
                continue
        if ending == "xml":
            r = util.get_response(url)
            if r is not False and util.check_if_xml(r):
                found = True
                xml_urls.append(url)
            else:
                continue
        if ending not in supported_endings:
            print(f"URL ending not recognized: {link}")
            # Test to see if it serves PDF or XML anyway
            r = util.get_response(url)
            if r is not False:
                if util.check_if_pdf(r):
                    found = True
                    pdf_urls.append(url)
                elif util.check_if_xml(r):
                    found = True
                    xml_urls.append(url) 
            else:
                continue 
    if found is False:
        print("No fulltext links found")
        return None
    else:
        return dict(
            pdf_urls=pdf_urls,
            xml_urls=xml_urls
        )


def handle_references(
        references: List[Dict[str, str]],
): 
    """Handles references and look up any DOIs found"""
    # print(references)
    # if not in_wikipedia:
    #     print("Skipping adding references since this DOI was not found in "+
    #           "any Wikipedia yet")
    # else:
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

def extract_data(message: Dict, in_wikipedia: bool = False):
    keys_we_want = ["author", "title", "original-title", "subtitle",
                    "publisher", "publisher-location", "score", "ISBN",
                    "reference", "license", "link", "URL", "ISSN", "issued"]
    data = {}
    # Extract data
    for key in message.keys():
        if key == "is-referenced-by-count":
            data[key] = message[key]
        if key == "ISBN":
            data[key] = message[key]
        if key == "ISSN":
            qid = wikidata.lookup_issn(message[key])
            if qid is not None:
                data[key] = qid
        if key == "issued":
            data[key] = message[key]
        if key == "publisher-location":
            data[key] = message[key]
        if key == "publisher":
            data[key] = message[key]
        if key == "references-count":
            data[key] = message[key]
        if key == "url":
            # What URL is this?
            data[key] = message[key]
        if key == "link":
            # This is fulltext links
            urls = None
            links: Dict = message["link"]
            if links is not None:
                urls = handle_links(links)
            if urls is not None:
                print(urls)
                data["urls"] = urls
        if key == "reference":
            if not in_wikipedia:
                print("Skipping adding references since this DOI was not found in "+
                      "any Wikipedia article yet")
            else:
                references: List[Dict[str, str]] = message[key]
                handle_references(references)
        if key == "license":
            # TODO detect garbage license URLs like
            # www.springer.com/tdm
            license_url = message[key]
            if license_url is None:
                print("No license found for this article")
        if key not in keys_we_want:
            print(f"Skipping key: {key} with data: {message[key]}")
    return data
            
def lookup_data(
        doi: str = None,
        in_wikipedia: bool = False,
): # -> Dict[str, str]:
    """Lookup data and return Dict"""
    # https://www.crossref.org/education/retrieve-metadata/rest-api/
    # async client here https://github.com/izihawa/aiocrossref but only 1 contributor
    # https://github.com/sckott/habanero >6 contributors not async
    if doi is None:
        print("Error. Got None instead of DOI. Report this error please.")
    else:
        print("Looking up from Crossref")
        cr = Crossref()
        #result = cr.works(doi=doi)
        result = cr.works(ids=doi)
        # print(result.keys())
        message = result["message"]
        object_type = message["type"]
        if object_type == "book":
            print("Book detected, we exclude those for now.")
            return None
        #print(message.keys())
        data = extract_data(message, in_wikipedia)
        print(data)
        if data.get("publisher") and data.get("publisher_location"): 
            # TODO look up publisher via sparqldataframe
            print("Found both publisher and location")

# lookup_data("")
# exit(0)
