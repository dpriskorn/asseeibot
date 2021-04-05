# Asynchronous Server Side Events External Identifier Bot
This bot follows the Wikimedia Eventstream and looks for Wikipedia pages with
DOI that are missing an item in Wikidata.

The goal of this bot is to help improve the collection of scientific articles in
Wikidata.

Currently all it does is to collect DOIs in a json file (see details below). These can be used with https://sourcemd.toolforge.org/index_old.php where they can be added seamlessly.

## Planned features
*Support for ISBN
*Import from Crossref.org and Worldcat.org if a non existing match is found.
*When importing DOIs it also imports all references that have DOIs.
*It saves a list of DOIs imported and checks if they have all the references
before marking them done.
*It completely ignores authors without ORCID and references without DOI.

## Installation
First clone the repo
 $ git clone ...

Then install the dependencies:

 $ sudo pip3 install -r requirements.txt
 $ sudo pip3 install git+https://github.com/dpriskorn/MediaWikiAPI
 $ sudo pip3 install git+https://github.com/ebraminio/aiosseclient

Please don't hold me accountable if the dependecies eat your dog. Look at their
sources and decide for yoursef whether to trust their authors and the code.

## Get DOIs for use in other tools
Install jq run the script and do

 $ cat found_in_wikipedia.json | jq 'keys'| jq -r '.[]'

They will be raw strings because of the "-r" argument. 

You can also follow them with 

$ watch "cat found_in_wikipedia.json | jq 'keys'| jq -r '.[]'"

# License
GPLv3 or later.
