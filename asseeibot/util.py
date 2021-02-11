#!/usr/bin/env python3
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


def check_if_xml(url: str) -> bool:
    # We don't trust blindly that the full text is still available
    print(f"Checking {url}") 
    r = requests.get(url)
    # inspect header to see if we got a PDF back
    # print(r.headers)
    if r.headers["Content-Type"] != "application/xml":
        print("Did not get XML, so it's probably not available")
        return False
    else:
        return True

def check_if_pdf(url: str) -> bool:
    # We don't trust blindly that the full text is still available
    print(f"Checking {url}") 
    r = requests.get(url)
    # inspect header to see if we got a PDF back
    # print(r.headers)
    if r.headers["Content-Type"] != "application/pdf":
        print("Did not get PDF, so it's probably not available")
        return False
    else:
        return True
