# vim: ts=4 : sw=4 : et

import json

from reading.gdocs import _parse_doc, changes


def test__parse_doc():
    with open("t/data/docs/books1.json") as fh:
        doc = json.load(fh)

    (lines, offsets) = _parse_doc(doc)
    assert lines == [
        "Adam Hochschild\n",
        "* King Leopold's Ghost\n",
        "\n",
        "Alan Moore\n",
        "* Watchmen\n",
        "\n",
        "Alan Warner\n",
        "* These Demented Lands\n",
        "\n",
        "Charles Dickens\n",
        "* Bleak House\n",
        "\n",
        "Erskine Childers\n",
        "* The Riddle of the Sands\n",
        "\n",
        "Eugene Vodolazkin\n",
        "* Laurus\n",
        "\n",
        "Kate Mosse\n",
        "* Citadel\n",
        "* Sepulchre\n",
        "* The Mistletoe Bride and Other Haunting Tales\n",
        "\n",
        "Kurt Vonnegut\n",
        "* Armageddon in Retrospect\n",
        "* Breakfast of Champions\n",
        "\n",
        "Terry Pratchett\n",
        "* Raising Steam\n",
        "* The Truth\n",
        "* The Wee Free Men\n",
        "* Unseen Academicals\n",
        "\n",
    ]
    assert offsets == [
        (1, 17),
        (17, 40),
        (40, 41),
        (41, 52),
        (52, 63),
        (63, 64),
        (64, 76),
        (76, 99),
        (99, 100),
        (100, 116),
        (116, 130),
        (130, 131),
        (131, 148),
        (148, 174),
        (174, 175),
        (175, 193),
        (193, 202),
        (202, 203),
        (203, 214),
        (214, 224),
        (224, 236),
        (236, 283),
        (283, 284),
        (284, 298),
        (298, 325),
        (325, 350),
        (350, 351),
        (351, 367),
        (367, 383),
        (383, 395),
        (395, 414),
        (414, 435),
        (435, 436),
    ]


def test_changes():
    with open("t/data/docs/books1.json") as fh:
        doc = json.load(fh)

    current, offsets = _parse_doc(doc)
    rev_id = doc["revisionId"]

    expected = [
        "Adam Hochschild\n",
        "* King Leopold's Ghost\n",
        "\n",
        "Alan Garner\n",
        "* The Owl Service\n",
        "\n",
        "Alan Warner\n",
        "* These Demented Lands\n",
        "\n",
        "Charles Brockden Brown\n",
        "* Wieland; or The Transformation, and Memoirs of Carwin, The Biloquist\n",
        "\n",
        "Charles Dickens\n",
        "* Bleak House\n",
        "\n",
        "\n",
        "Eugene Vodolazkin\n",
        "* Laurus\n",
        "\n",
        "Kate Mosse\n",
        "* Citadel\n",
        "* Sepulchre\n",
        "* The Burning Chambers\n",
        "* The Mistletoe Bride and Other Haunting Tales\n",
        "\n",
        "Kurt Vonnegut Jr.\n",
        "* Armageddon in Retrospect\n",
        "* Breakfast of Champions\n",
        "\n",
        "Terry Pratchett\n",
        "* Raising Steam\n",
        "* The Wee Free Men\n",
        "* Unseen Academicals\n",
    ]

    c = changes(rev_id, current, offsets, expected)

    assert c == {
        "requests": [
            {"deleteContentRange": {"range": {"endIndex": 436, "startIndex": 435}}},
            {"deleteContentRange": {"range": {"endIndex": 395, "startIndex": 383}}},
            {"deleteContentRange": {"range": {"endIndex": 298, "startIndex": 284}}},
            {"insertText": {"location": {"index": (284, 298)}, "text": "Kurt Vonnegut Jr.\n"}},
            {"insertText": {"location": {"index": (236, 283)}, "text": "* The Burning Chambers\n"}},
            {"deleteContentRange": {"range": {"endIndex": 174, "startIndex": 131}}},
            {
                "insertText": {
                    "location": {"index": (100, 116)},
                    "text": (
                        "Charles Brockden Brown\n"
                        "* Wieland; or The Transformation, and Memoirs of Carwin, The Biloquist\n\n"
                    ),
                }
            },
            {"deleteContentRange": {"range": {"endIndex": 63, "startIndex": 41}}},
            {
                "insertText": {
                    "location": {"index": (41, 52)},
                    "text": "Alan Garner\n* The Owl Service\n",
                }
            },
        ],
        "writeControl": {
            "requiredRevisionId": (
                "AOV_f48jtrnaJS70zG3tqgVShUQVCQseXYV6KVeT91"
                "bzb9IgXehnfjimaEAbKz4B35_IucCYyxVlPjM2LQxv"
            ),
        },
    }
