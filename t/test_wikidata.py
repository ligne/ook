# vim: ts=4 : sw=4 : et

from __future__ import annotations

import json

import reading.wikidata
from reading.wikidata import Entity, _format_search_results, _uc_first


def test__uc_first() -> None:
    tests = [
        ["test", "Test"],
        ["Test", "Test"],
        ["Test", "Test"],
        ["TEST", "TEST"],
        ["t", "T"],
        ["", ""],
    ]

    for string, expected in tests:
        assert _uc_first(string) == expected


################################################################################


def test_format_search_results() -> None:
    with open("t/data/wikidata/search/george-sand.json") as fh:
        j = json.load(fh)

    assert _format_search_results(j) == [
        {
            "Label": "George Sand",
            "QID": "Q3816",
            "Description": "French novelist and memoirist; pseudonym of Lucile Aurore Dupin",
        },
        {
            "Label": "George Sand",
            "QID": "Q61043695",
            "Description": 'Theatrical character of the play "An Angel in my Way"',
        },
        {
            "Label": "George Sand",
            "QID": "Q18191141",
            "Description": "Sculpture by François Sicard",
        },
        {
            "Label": "George Sand",
            "QID": "Q19199114",
            "Description": "German article in Die Gartenlaube, 1854, no. 41",
        },
        {
            "Label": "George Sand",
            "QID": "Q57317014",
            "Description": "Edition by Thomas",
        },
        {
            "Label": "George Sand",
            "QID": "Q62611778",
            "Description": "German article in Die Gartenlaube, 1861, no. 17",
        },
        {
            "Label": "George Sand",
            "QID": "Q75101202",
            "Description": "Wikimedia disambiguation page",
        },
    ]


def test_format_search_results_no_results() -> None:
    with open("t/data/wikidata/search/justin-pearce.json") as fh:
        j = json.load(fh)

    assert _format_search_results(j) == []


################################################################################


def _load_entity(qid: str):
    with open(f"t/data/wikidata/entities/{qid}.json") as fh:
        return Entity(json.load(fh)["entities"][qid])


reading.wikidata.entity = _load_entity


def test_entity() -> None:
    entity = _load_entity("Q12807")
    assert entity.qid == "Q12807"
    assert entity.label == "Umberto Eco"
    assert (
        entity.description
        == "Italian semiotician, essayist, philosopher, literary critic, and novelist"
    )
    assert entity.gender == "male"
    assert entity.nationality == "it"

    entity = _load_entity("Q276032")
    assert entity.qid == "Q276032"
    assert entity.label == "Edith Wharton"
    assert entity.description == "American novelist, short story writer, designer"
    assert entity.gender == "female"
    assert entity.nationality == "us"

    entity = _load_entity("Q8018")
    assert entity.qid == "Q8018"
    assert entity.label == "Augustine of Hippo"
    assert entity.description == "Early Christian theologian, philosopher and Church Father"
    assert entity.gender == "male"
    assert entity.nationality == "Ancient Rome"

    entity = _load_entity("Q3302368")
    assert entity.label == "Max de Radiguès"
    assert entity.description == "", "Empty description"


def test_entity_collective() -> None:
    entity = _load_entity("Q2662892")
    assert entity.qid == "Q2662892"
    assert entity.label == "Boileau-Narcejac"
    assert entity.description == "Team of French writers"
    assert entity.gender is None
    assert entity.nationality is None
