from typing import List
from thefuzz import process, fuzz


def get_best_match(queries: List[str], choices: List[str], string_processor=lambda x : x) -> List[str]:
    assert isinstance(queries, list)
    assert isinstance(choices, list)
    picks = []
    for c in queries:
        ans = process.extractOne(string_processor(c), choices, processor=string_processor)
        picks.append([c, ans[0], ans[1]])
    #print(f"\nqueries: {queries} best match: {max(picks, key=lambda x : x[2])} to_match: {choices}\n")
    return max(picks, key=lambda x : x[2])


def get_highest_possible_match(match: str, to_match: str, string_processor=lambda x : x) -> int:
    assert isinstance(match, str)
    assert isinstance(to_match, str)
    un_modified_match = match
    to_match = string_processor(to_match)
    match = string_processor(match)
    scores = []
    for i in range(len(to_match)):
        to_match = to_match[:-1]
        scores.append(fuzz.ratio(match, to_match))
    #print(f"\nun_modified_match: {un_modified_match} to_match: {to_match} scores: {scores}\n")
    return un_modified_match, max(scores)