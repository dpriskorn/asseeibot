#!/usr/bin/env python3
import sys
# Workaround for 3.7 missing Literal see https://python.plainenglish.io/the-literal-annotation-in-python-f882c021ab53
if sys.version_info.major == 3 and sys.version_info.minor == 7:
    from typing import Union
    from typing_extensions import Literal
else:
    from typing import Union, Literal

import requests


def yes_no_question(message: str):
    # https://www.quora.com/
    # I%E2%80%99m-new-to-Python-how-can-I-write-a-yes-no-question
    # this will loop forever
    while True:
        answer = input("{} [Y/n]: ".format(message))
        if len(answer) == 0 or answer[0].lower() in ('y', 'n'):
            if len(answer) == 0:
                return True
            else:
                # the == operator just returns a boolean,
                return answer[0].lower() == 'y'


def get_response(url: str) -> Union[requests.models.Response, Literal[False]]:
    print(f"Checking {url}")
    r = requests.head(url)
    if r.status_code == 200:
        return r
    elif r.status_code == 301:
        # This is permanently moved.
        # See e.g. https://www.journals.uchicago.edu/doi/pdf/10.1086/243149
        return False
    elif r.status_code == 403:
        # This is forbidden.
        # See e.g.
        # https://onlinelibrary.wiley.com/doi/full/10.1002/elan.200390114
        return False
    else:
        print(f"Unknown response code {r.status_code}")
        return False


def check_if_xml(response) -> bool:
    # We don't trust blindly that the full text is still available
    # inspect header to see if we got XML back
    if response.headers.get("Content-Type"):
        if response.headers["Content-Type"] != "application/xml":
            print("Did not get XML, so it's probably not available")
            return False
        else:
            return True
    else:
        return False


def check_if_pdf(response) -> bool:
    # We don't trust blindly that the full text is still available
    # inspect header to see if we got a PDF back
    if response.headers.get("Content-Type"):
        if response.headers["Content-Type"] != "application/pdf":
            print("Did not get PDF, so it's probably not available")
            return False
        else:
            return True
    else:
        return False
