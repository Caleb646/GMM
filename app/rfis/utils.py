from collections import OrderedDict
from typing import List
from thefuzz import process, fuzz



def get_best_match(to_compare: List[str], choice: str, min_score=60) -> str:
    picks = OrderedDict()
    for c in to_compare:
        picks[c] = fuzz.ratio(c, choice)
    best_pick = max(picks, key=picks.get)
    if picks[best_pick] > min_score:
        return best_pick
    return ""