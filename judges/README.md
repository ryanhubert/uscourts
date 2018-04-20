# fed-judge-data

## Files contained in package

`LoadData.py` provides two functions: (1) `UpdateData` which downloads the FJC's biographical database, generates a python dictionary (referred to as the `fjc_dict`) and saves as a json file; and (2) `LoadData` which loads a local json previously generated using the `UpdateData` function. The latter function enables users to preserve a previous version of the FJC database and avoids the need for network connection every time data is loaded.

`QueryTools.py` provides a set of tools that are useful for querying `fjc_dict` and generating lists of judges meeting specific criteria.

`NameFinder.py` contains a function `NameFinder` that takes a dictionary of first/middle/last names and an unstructured text string and finds names from the dictionary in the unstructured text. This function works in lieu of a part of speech (POS) tagger or named entity recognizer (NER), such as the Stanford NER (which is implemented in `nltk`). Indeed, unlike a POS tagger or NER, the `NameFinder` function leverages a predefined database of names and flexibly searches over unstructured text to find utterances of these names. **Update 04/11/2018**: NameFinder v2 is now out. It has been completely re-written to dramatically improve performance. Speed tests demonstrate it is nearly twice as fast as v1. Additional options added to improve accuracy. See detailed notes in the script.



## For future versions

- Currently working on a tool to generate a `csv` file containing key information about judges' work histories, education, and nominations.

- Expand data to include magistrate judges and territorial judges.
