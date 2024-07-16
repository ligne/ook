# vim: ts=4 : sw=4 : et

"""Output to Google Docs."""

from __future__ import annotations

from difflib import SequenceMatcher
import json
import pickle

from google.auth.transport.requests import AuthorizedSession, Request
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import Config
from .reports import _process_report


# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/documents"]
TOKEN_FILE = "data/google.token"
CREDS_FILE = "data/credentials.json"


################################################################################


# authenticate
def get_session():
    """Return a Google Docs session, requesting access if necessary."""
    # stores the user's access and refresh tokens, and is created automatically
    # when the authorization flow completes for the first time.
    try:
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    except FileNotFoundError:
        creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES).run_local_server(
                port=0
            )

        # Save the credentials for the next run
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return AuthorizedSession(creds)


# FIXME create it if necessary?
def get_document(session, doc_id):
    """Return the contents of $doc_id."""
    return session.get(f"https://docs.googleapis.com/v1/documents/{doc_id}").json()


# apply $changes to $doc_id
def submit_changes(session, doc_id, payload):
    """Apply changes to $doc_id."""
    resp = session.post(
        f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate", json=payload
    )

    if not resp.ok:
        print(json.dumps(resp.json()))


################################################################################


# parse the document's content into something that can be compared
#
# we want something that can be used by difflib (and therefore must be
# hashable).  we also need to track their start and end indices, but we
# obviously don't want these to affect the hash.
#
# currently this is done by building two parallel lists, one of the content and
# the other of the offsets in the original document
def _parse_doc(doc):
    strings = []
    offsets = []

    for element in doc["body"]["content"]:
        if "paragraph" in element:
            strings.append(_para_contents(element["paragraph"]))
            offsets.append(_para_offsets(element))
        elif "sectionBreak" in element:
            # these Just Exist
            pass
        else:
            print(element.keys())

    return (strings, offsets)


def _para_contents(paragraph):
    return "".join([e["textRun"]["content"] for e in paragraph["elements"]])


def _para_offsets(element):
    return (element["startIndex"], element["endIndex"])


################################################################################


def _insert_text_request(start, lines):
    return {
        "insertText": {
            "text": "".join(lines),
            "location": {
                "index": start,
            },
        }
    }


def _delete_content_request(offset_range):
    return {
        "deleteContentRange": {
            "range": {
                "startIndex": offset_range[0][0],
                "endIndex": offset_range[-1][1],
            }
        }
    }


def changes(rev_id, got, offsets, expected):
    """Return a changeset for submission to Google Docs."""
    seq = SequenceMatcher(None, got, expected)

    requests = []

    for tag, got1, got2, exp1, exp2 in seq.get_opcodes()[::-1]:
        if tag == "equal":
            continue
        elif tag == "delete":
            requests.append(_delete_content_request(offsets[got1:got2]))
        elif tag == "insert":
            requests.append(_insert_text_request(offsets[got1], expected[exp1:exp2]))
        elif tag == "replace":
            requests.append(_delete_content_request(offsets[got1:got2]))
            requests.append(_insert_text_request(offsets[got1], expected[exp1:exp2]))

    return {
        "requests": requests,
        "writeControl": {
            "requiredRevisionId": rev_id,
        },
    }


################################################################################


def _display_report(df):
    g = df.sort_values(["Author", "Title"]).groupby("Author")
    for author, books in g:
        yield "{}\n".format(author)
        for book in books.itertuples():
            yield "* {}\n".format(book.Title)
        yield "\n"


def main(config: Config) -> None:
    expected = []
    for df in _process_report(config("reports.docs")):
        expected.extend(_display_report(df))

    doc_id = "1_bL2hGaP03TQj5AVKUWZxUwehSIrkmXIR_aGGqFJWWo"  # FIXME

    session = get_session()
    doc = get_document(session, doc_id)

    rev_id = doc["revisionId"]
    current, offsets = _parse_doc(doc)

    c = changes(rev_id, current, offsets, expected)

    del c["requests"][0]  # avoid deleting the trailing newline FIXME
    print(str(json.dumps(c["requests"])))

    submit_changes(session, doc_id, c)


if __name__ == "__main__":
    main(Config.from_file())
