# Asynchronous Server Side Events External Identifier Bot
![bild](https://user-images.githubusercontent.com/68460690/151193195-648d79c5-c6c2-4825-b3df-eea3727bf5e6.png)
*Example output from the tool.*

This bot follows the Wikimedia Eventstream (from Kafka) and looks for Wikipedia pages with
DOI that are missing an item in Wikidata.

The goal of this bot is to help improve the collection of scientific articles in
Wikidata. Currently according to estimates based on 1000 random edits is that around 
75% of all DOIs used in the English Wikipedia are currently missing in Wikidata. 


Currently all it does is to collect DOIs in a json file (see details below). 
These can be used with https://sourcemd.toolforge.org/index_old.php where they 
can be added seamlessly.

The development was paused in 2021 because the Wikidata infrastructure is not 
ready to handle all the new items and triples that this bot would create over time.

As of december 2021 WMF is trying to fix the scaling issues surrounding BlazeGraph. 
See https://phabricator.wikimedia.org/T206560

In january 2022 following interest from the Internet Archive the development was 
resumed and it got new features like a 
[fuzzy-powered named-entity recognition matcher with science ontology](https://www.wikidata.org/wiki/Q110733873) 
and an upload function using the fantastic library WikibaseIntegrator.

## Installation
First clone the repo
 $ git clone ...

Then install the dependencies:

 $ sudo pip3 install -r requirements.txt

Please don't hold me accountable if the dependecies eat your dog. Look at their
sources and decide for yourself whether to trust their authors and the code.

## Configuration
Edit the config.py file in the asseeibot/ directory and add your WMF username there.

## What I learned from this project
* This was the second time I dipped my toes in asynchronous programming. 
  It was fun and challenging thanks to the framework I used. 
* I ran into some issues with a library for parsing the Wikipedia page and reported the issue upstream. 
  Waiting for a solution there I hacked the library code locally and got it to work :)
  Then I switched to pywikibot to get better support for template parsing.
* I used pywikibot for the first time. It seems to do a good job of fetching data 
  from Wikipedia and parsing it, so I can extract the templates.
  Unfortunately it seems to be difficult to turn off the verbose logging, so I don't like it much.
* I tried completely avoiding strings outside of variables in config and enums for the first time. 
  It makes it easier to debug, read and refactor the code.
* I used the imminent class validation library pydantic for the first time. What a wonderful tool!

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
