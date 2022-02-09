import logging
from unittest import TestCase

from asseeibot.models.crossref_engine.ontology_based_ner_matcher import OntologyBasedNerMatcher, FuzzyMatch
from asseeibot.models.enums import OntologyDataframeColumn

logging.basicConfig(level=logging.INFO)


class TestOntology(TestCase):

    def test_calculate_scores(self):
        logger = logging.getLogger(__name__)
        subject = "Petrology"
        ontology = OntologyBasedNerMatcher(
            match=FuzzyMatch(
                crossref_subject=subject,
                original_subject=subject,
                split_subject=False
            ))
        ontology.__get_the_dataframe_from_config__()
        ontology.__calculate_scores__()
        ontology.__sort_dataframe__(OntologyDataframeColumn.LABEL_SCORE)
        logger.info("score ", ontology.dataframe["label_score"].head(1).values[0])
        if ontology.dataframe["label_score"].head(1).values[0] == 100:
            assert True
        else:
            self.fail()
