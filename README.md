# Asynchronous Server Side Events External Identifier Bot
This bot follows the Wikimedia Eventstream and looks for Wikipedia pages with
DOI or ISBN that are missing an item in Wikidata.

It imports from Crossref.org and Worldcat.org if a non existing match is found.

When importing DOIs it also imports all references that have DOIs and all their references that have DOIs... recursively. That means that it can quickly become a lot to import.

It saves a list of DOIs imported and checks if they have all the references before marking them done.
