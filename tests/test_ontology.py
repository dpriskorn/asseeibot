import logging
from unittest import TestCase

from asseeibot.models.ontology_dataframe import OntologyDataframeSetup
from asseeibot.models.enums import OntologyDataframeColumn
from asseeibot.models.fuzzy_match import FuzzyMatch
from asseeibot.models.ontology import Ontology

logging.basicConfig(level=logging.INFO)


class TestOntology(TestCase):

    def test_calculate_scores(self):
        logger = logging.getLogger(__name__)
        subject = "Petrology"
        dataframe = OntologyDataframeSetup()
        dataframe.prepare_the_ontology_pickled_dataframe()
        ontology = Ontology(
            match=FuzzyMatch(
                subject=subject,
                original_subject=subject
            ))
        ontology.__get_the_dataframe_from_config__()
        ontology.__calculate_scores__()
        ontology.__sort_dataframe__(OntologyDataframeColumn.LABEL_SCORE)
        logger.info("score ", ontology.dataframe["label_score"].head(1).values[0])
        if ontology.dataframe["label_score"].head(1).values[0] == 100:
            assert True
        else:
            self.fail()

