from asseeibot import runtime_variables


def prepare_the_ontology_pickled_dataframe():
    # self.__download_the_ontology_pickle__()
    if runtime_variables.ontology_dataframe is None:
        # This pickle is ~4MB in size and takes less than a second to load.
        # noinspection PyUnresolvedReferences
        dataframe: Dataset["item", "itemLabel", "alias"] = pd.read_pickle("ontology.pkl")
        # This is needed for the fuzzymatching to work properly
        runtime_variables.ontology_dataframe = dataframe.fillna('')
