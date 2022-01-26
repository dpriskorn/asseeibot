# Asynchronous Server Side Events External Identifier Bot
This bot follows the Wikimedia Eventstream (from Kafka) and looks for Wikipedia pages with
DOI that are missing an item in Wikidata.

The goal of this bot is to help improve the collection of scientific articles in
Wikidata.

Currently all it does is to collect DOIs in a json file (see details below). 
These can be used with https://sourcemd.toolforge.org/index_old.php where they 
can be added seamlessly.

The development was paused in 2021 because the Wikidata infrastructure is not 
ready to handle all the new items and triples that this bot would create over time.

As of december 2021 WMF is trying to fix the scaling issues surrounding BlazeGraph. 
See https://phabricator.wikimedia.org/T206560

## What I learned from this project
This was the second time I dipped my toes in asynchronous programming. 
It was fun and challanging thanks to the framework I used. 
I ran into some issues with a library for parsing the Wikipedia page and reported the issue upstream. 
Waiting for a solution there I hacked the library code locally and got it to work :)

## TODO once WMF fixed the infrastructure
*Support for ISBN
*Import from Crossref.org and Worldcat.org if a non existing match is found.
*When importing DOIs it also imports all references that have DOIs.
*It saves a list of DOIs imported and checks if they have all the references
before marking them done.

## Installation
First clone the repo
 $ git clone ...

Then install the dependencies:

 $ sudo pip3 install -r requirements.txt

Please don't hold me accountable if the dependecies eat your dog. Look at their
sources and decide for yourself whether to trust their authors and the code.

## Get DOIs for use in other tools (Linux)
Make sure you have `jq` installed and run the following command line in a Linux terminal.

 $ cat found_in_wikipedia.json | jq 'keys'| jq -r '.[]'

They will be raw strings because of the "-r" argument. 

You can also follow them with 

$ watch "cat found_in_wikipedia.json | jq 'keys'| jq -r '.[]'"

# License
GPLv3 or later.
