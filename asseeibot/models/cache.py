import logging
from os.path import exists
from typing import Optional

import pandas as pd
from pydantic import BaseModel

import config

logger = logging.getLogger(__name__)

# This code is adapted from https://github.com/dpriskorn/WikidataMLSuggester and LexUtils

# lookups where inspired by
# https://stackoverflow.com/questions/24761133/pandas-check-if-row-exists-with-certain-values


class Cache(BaseModel):
    @staticmethod
    def read(label: str) -> Optional[str]:
        """Returns None or result from the cache"""
        if label is None:
            raise ValueError("did not get all we need")
        if label is "":
            raise ValueError("label was empty string")
        logger.debug("Reading from the cache")
        if exists(config.cache_pickle_filename):
            df = pd.read_pickle(config.cache_pickle_filename)
            # This tests whether any row matches
            match = (df['label'] == label).any()
            logger.debug(f"match:{match}")
            if match:
                # Here we find the row that matches and extract the
                # result column and extract the value using any()
                result = df.loc[df["label"] == label, "qid"][0]
                logger.debug(f"result:{result}")
                if result is not None:
                    return result

    @staticmethod
    def add(label: str, qid: str) -> None:
        if label is "":
            raise ValueError("label was empty string")
        if qid is None:
            raise ValueError("qid was None")
        if qid is "":
            raise ValueError("qid was empty string")
        logger.debug("Adding to cache")
        data = dict(qid=qid, label=label)
        if exists(config.cache_pickle_filename):
            df = pd.read_pickle(config.cache_pickle_filename)
            # This tests whether any row matches
            match = (df['label'] == label).any()
            logger.debug(f"match:{match}")
            if not match:
                # We only give save the value once for now
                df = df.append(pd.DataFrame(data=[data]))
                logger.debug(f"Saving pickle with new label {label}")
                df.to_pickle(config.cache_pickle_filename)
        else:
            pd.DataFrame(data=[data]).to_pickle(config.cache_pickle_filename)
