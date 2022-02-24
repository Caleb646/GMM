import re
from thefuzz import fuzz
from thefuzz import process

test_strings = [
    "RE: RFIs Test Job 12/36/1200 Hello All", "Re: RFI TestJob", "RE RFI TestJob", 
    "FW: RFI TestJob", "Fw: RFI TestJob", "FW RFI TestJob"
    ]


pattern = r'(RE|Re|FW|Fw|:)'
choices = ("RFI", 'Submittal')
job_names = ('Test Job', 'SC Fairfield')
scores = []

chosen = {}
best_subject_line_match_dict = {}

def choose_thread_type(subject_line):
    strings = subject_line.split(" ")
    choice = None
    subject_line_match = None
    high_score = 0
    for c in choices:
        ans = process.extractOne(c, strings)
        if ans[1] > high_score:
            high_score = ans[1]
            choice = c
            subject_line_match = ans[0]
    if high_score <= 65:
        chosen['threadType'] = 'Unknown'
    else:
        chosen['threadType'] = choice
    best_subject_line_match_dict['threadType'] = subject_line_match

def choose_job_name(subject_line):
    highest_score = 0
    best_choice = None
    best_subject_line_match = None
    string = re.sub(best_subject_line_match_dict['threadType'], "", subject_line).strip()
    for j in job_names:
        prev_score = 0
        prev_subject_line_match = None

        current_score = fuzz.ratio(j, string)   
        current_subject_line_match = string

        count = len(string)
        while current_score > prev_score and count >= 0:
            prev_score = current_score
            prev_subject_line_match = current_subject_line_match

            current_subject_line_match = current_subject_line_match[:-1] #remove last character
            current_score = fuzz.ratio(j, current_subject_line_match)

            count -= 1

            scores.append((prev_score, current_score))
        if prev_score > highest_score:
            highest_score = prev_score
            best_choice = j
            best_subject_line_match = prev_subject_line_match
    print(highest_score)
    if highest_score <= 50:
        chosen['jobName'] = 'Unknown'
    else:
        chosen['jobName'] = best_choice
    best_subject_line_match_dict['jobName'] = best_subject_line_match

choose_thread_type(test_strings[0])
choose_job_name(test_strings[0])
print(chosen, best_subject_line_match_dict)
print(scores)