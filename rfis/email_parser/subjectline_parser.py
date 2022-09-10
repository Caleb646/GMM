import re

from constance import config

from .. import constants as c
from .. import models as m
from .. import utils as u
from .base_parsers import BaseParser


class SubjectLineParser(BaseParser):
    RE_FW_PATTERN = re.compile(r"^(RE|Re|FW|FWD|Fw|):?\s")

    def __init__(self) -> None:
        super().__init__()
        self.THREAD_TYPE_CHOICES = [mt.name for mt in m.ThreadType.objects.all()]
        self.JOB_NAMES = [j.name for j in m.Job.objects.all()]
        self._min_score_allowed = config.SUBJECT_LINE_PARSER_CONFIDENCE
        self._best_subject_line_match = {}

    def parse(self, subject_line):
        self._clear()
        # have to clean the subject line first before anything else
        self._clean_subject_line(subject_line)
        self._choose_thread_type()
        self._choose_job_name()
        self._is_parsed = True

    def _clear(self):
        self._best_subject_line_match.clear()
        super()._clear()

    def _clean_subject_line(self, subject_line):
        self._subject_line = re.sub(self.RE_FW_PATTERN, "", subject_line).strip()

    def _choose_thread_type(self):
        best_match, best_choice, score = u.get_best_match(
            self.THREAD_TYPE_CHOICES,
            self._subject_line.split(" "),
            lambda x: x.strip().lower(),
        )

        if score > self._min_score_allowed:
            self._chosen["threadType"] = best_match
        else:
            self._chosen["threadType"] = c.FIELD_VALUE_UNKNOWN_THREAD_TYPE

    def _choose_job_name(self):
        # TODO could use binary sort to make more efficient
        best_match, best_choice, bscore = u.get_best_match(
            self.JOB_NAMES, [self._subject_line], lambda x: x.lower().replace(" ", "")
        )
        unmodified_match, score = u.get_highest_possible_match(
            best_match, self._subject_line, lambda x: x.lower().replace(" ", "")
        )
        if score > self._min_score_allowed or bscore > self._min_score_allowed:
            self._chosen["jobName"] = unmodified_match
        else:
            self._chosen["jobName"] = c.FIELD_VALUE_UNKNOWN_JOB

        # print(f"\n\nsubject chosen: {self._chosen}")

    @property
    def parsed_subject_line(self):
        assert self._is_parsed
        return self._subject_line

    @property
    def thread_type(self):
        assert self._is_parsed
        return self._chosen.get("threadType", c.FIELD_VALUE_UNKNOWN_THREAD_TYPE)

    @property
    def job_name(self):
        assert self._is_parsed
        return self._chosen.get("jobName", c.FIELD_VALUE_UNKNOWN_JOB)
