# Asynchronous Server Side Events External Identifier Bot
This bot follows the Wikimedia Eventstream and looks for Wikipedia pages with
DOI or ISBN that are missing an item in Wikidata.

The goal of this bot is to improve the collection of scientific articles in
Wikidata.

It imports from Crossref.org and Worldcat.org if a non existing match is found.

When importing DOIs it also imports all references that have DOIs.

It saves a list of DOIs imported and checks if they have all the references
before marking them done.

It completely ignores authors without ORCID and references without DOI.

## Installation
First clone the repo
 $ git clone ...

Then install the dependencies
 $ sudo pip install -r requirements.txt

Please don't hold me accountable if the dependecies eat your dog. Look at their
sources and decide for yoursef whether to trust their authors and the code.

## Get DOIs for use in other tools
Install jq run the script and do
 $ cat found_in_wikipedia.json | jq 'keys'| jq -r '.[]'
They will be raw strings because of the "-r" argument. 

You can also follow them with 
 $ watch "cat found_in_wikipedia.json | jq 'keys'| jq -r '.[]'"
