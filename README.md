# Asynchronous Server Side Events External Identifier Bot
*Warning this is alpha software and EditGroups are not supported yet. It can potentially make 
thousands of bad edits in a short period*

![bild](https://user-images.githubusercontent.com/68460690/151681324-040de41b-bdea-488b-8c5b-be509e1163b1.png)
*Example output from the tool.*

This bot follows the Wikimedia Eventstream (from Kafka) and looks for Wikipedia pages with
DOI that are missing an item in Wikidata.

The goal of this bot is to help improve the collection of scientific articles in
Wikidata. Currently according to estimates based on 1000 random edits is that around 
10-15% of all DOIs used in the English Wikipedia are currently missing in Wikidata. 

## Features
* Matching of Crossref subjects to Wikidata Entities with caching using a custom domain ontology
* Upload of the matches to Wikidata
* Output of DOIs missing in Wikidata to the screen for use with other tools like SourceMD
* Delete a match from the cache

### Delete a match
The tool support deleting matches from the cache. That makes it easier for 
the user to avoid uploading garbage matches 
if a match has been approved in error.

### Domain-ontology-based fuzzy-powered named-entity recognition matcher
This is a fancy new algorithm I invented inspired by reading a few papers 
about topic modeling, ontology-based relation extraction, named-entity recognition
and use of machine learning methods in these fields.

It does not use ML, but instead a Levenshtein distance and a "hand crafted" ontology. 
The result is surprisingly accurate and the matches on labels are often dead on.

This is all thanks to the thousands of volunteers in Wikidata who have worked on the 
4 subgraphs that comprise the ontology:
* academic disciplines
* branches of science
* YSO links
* Library of congress classification links

Version 3 of the ontology has ~26k Wikidata items out of which ~23k
have a description and ~13k have at least one alias

You can generate/download it using the queries in `queries/` simply paste them in WDQS.
See https://www.wikidata.org/wiki/Q110733873

Inclusion of two more subgraphs are also planned but not done because of timeouts:
* field of study/studies
* field of work

See queries/big_ontology_query.sparql

## Installation
First clone the repo
 $ git clone ...

Then install the dependencies:

 $ sudo pip3 install -r requirements.txt

Please don't hold me accountable if the dependencies eat your dog. Look at their
sources and decide for yourself whether to trust their authors and the code.

## Configuration
Edit the config.py file in the asseeibot/ directory and add your WMF username there.

## Diagrams
These were made using the excellent [PlanUML](https://plantuml.com/index) plugin to PyCharm
### Sequence diagram
![bild](https://user-images.githubusercontent.com/68460690/152224991-b84b268a-ff60-4ea6-99a0-897c8c7f699d.png)
### Class hierarchy diagram
![bild](https://user-images.githubusercontent.com/68460690/152242344-b1debfc1-3ae1-4a8c-968c-92dfe43f96bc.png)

## History
The development was paused in 2021 because the Wikidata infrastructure is not 
ready to handle all the new items and triples that this bot would create over time.

As of december 2021 WMF is trying to fix the scaling issues surrounding BlazeGraph. 
See https://phabricator.wikimedia.org/T206560

In january 2022 following interest from the Internet Archive the development was 
resumed and it got new features like a 
[fuzzy-powered named-entity recognition matcher with science ontology](https://www.wikidata.org/wiki/Q110733873) 
and an upload function using the fantastic library WikibaseIntegrator.

## What I learned from this project
* This was the second time I dipped my toes in asynchronous programming. 
  It was fun and challenging thanks to the framework I used. 
* I made my first 2 diagrams using PlanUML. It really helps getting an overview of the flow of the program and the relations between the classes.
* I ran into some issues with a library for parsing the Wikipedia page and reported the issue upstream. 
  Waiting for a solution there I hacked the library code locally and got it to work :)
  Then I switched to pywikibot to get better support for template parsing.
* I used pywikibot for the first time. It seems to do a good job of fetching data 
  from Wikipedia and parsing it, so I can extract the templates.
  Unfortunately it seems to be difficult to turn off the verbose logging, so I don't like it much.
* I tried completely avoiding strings outside of variables in config and enums for the first time. 
  It makes it easier to debug, read and refactor the code.
* I used the class validation library pydantic for the first time. Unfortunately it seems that it has some issues with lazy evaluation of imports so I get errors out of the box :/ 
* I used Rich tables for better output to the console. It even support links!

## TODO once WMF fixed the infrastructure or a proper Wikibase for all of science has been set up
* Support for ISBN
* Import from Crossref.org and Worldcat.org if a non existing match is found.
* When importing DOIs it also imports all references that have DOIs.
* It saves a list of DOIs imported and checks if they have all the references
before marking them done.

## Kubernetes
*Note:At the moment it only outputs to screen and the matching requires user interaction, 
so it does not make much sense to run it in k8s.*

It is possible to run the tool in the WMC Kubernetes cluster if you want. 
Follow the guide I wrote for ItemSubjector to set it up and run `./create_job.sh 1` 
to start a job.

# License
GPLv3 or later.
