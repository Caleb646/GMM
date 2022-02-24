import re
from thefuzz import process, fuzz

from .models import MessageThread, Job

# Code was taken from here: https://github.com/zapier/email-reply-parser and modified
class EmailReplyParser(object):
    """ Represents a email message that is parsed.
    """

    @staticmethod
    def read(text):
        """ Factory method that splits email into list of fragments

            text - A string email body

            Returns an EmailMessage instance
        """
        return EmailMessage(text).read()

    @staticmethod
    def parse_reply(text):
        """ Provides the reply portion of email.

            text - A string email body

            Returns reply body message
        """
        return EmailReplyParser.read(text).reply


class EmailMessage(object):
    """ An email message represents a parsed email body.
    """

    SIG_REGEX = re.compile(r'(--|__|-\w)|(^Sent from my (\w+\s*){1,3})')
    QUOTE_HDR_REGEX = re.compile('On.*wrote:$')
    QUOTED_REGEX = re.compile(r'(>+)')
    HEADER_REGEX = re.compile(r'^\*?(From|Sent|To|Subject):\*? .+')
    _MULTI_QUOTE_HDR_REGEX = r'(?!On.*On\s.+?wrote:)(On\s(.+?)wrote:)'
    MULTI_QUOTE_HDR_REGEX = re.compile(_MULTI_QUOTE_HDR_REGEX, re.DOTALL | re.MULTILINE)
    MULTI_QUOTE_HDR_REGEX_MULTILINE = re.compile(_MULTI_QUOTE_HDR_REGEX, re.DOTALL)

    def __init__(self, text):
        self.fragments = []
        self.fragment = None
        self.text = text.replace('\r\n', '\n')
        self.found_visible = False

    def read(self):
        """ Creates new fragment for each line
            and labels as a signature, quote, or hidden.

            Returns EmailMessage instance
        """

        self.found_visible = False

        is_multi_quote_header = self.MULTI_QUOTE_HDR_REGEX_MULTILINE.search(self.text)
        if is_multi_quote_header:
            self.text = self.MULTI_QUOTE_HDR_REGEX.sub(is_multi_quote_header.groups()[0].replace('\n', ''), self.text)

        # Fix any outlook style replies, with the reply immediately above the signature boundary line
        #   See email_2_2.txt for an example
        self.text = re.sub('([^\n])(?=\n ?[_-]{7,})', '\\1\n', self.text, re.MULTILINE)

        self.lines = self.text.split('\n')
        self.lines.reverse()

        for line in self.lines:
            self._scan_line(line)

        self._finish_fragment()

        self.fragments.reverse()

        return self

    @property
    def reply(self):
        """ Captures reply message within email
        """
        reply = []
        for f in self.fragments:
            if not (f.hidden or f.quoted):
                reply.append(f.content)
        return '\n'.join(reply)

    def _scan_line(self, line):
        """ Reviews each line in email message and determines fragment type

            line - a row of text from an email message
        """
        is_quote_header = self.QUOTE_HDR_REGEX.match(line) is not None
        is_quoted = self.QUOTED_REGEX.match(line) is not None
        is_header = is_quote_header or self.HEADER_REGEX.match(line) is not None

        if self.fragment and len(line.strip()) == 0:
            if self.SIG_REGEX.match(self.fragment.lines[-1].strip()):
                self.fragment.signature = True
                self._finish_fragment()

        if self.fragment \
                and ((self.fragment.headers == is_header and self.fragment.quoted == is_quoted) or
                         (self.fragment.quoted and (is_quote_header or len(line.strip()) == 0))):

            self.fragment.lines.append(line)
        else:
            self._finish_fragment()
            self.fragment = Fragment(is_quoted, line, headers=is_header)

    def quote_header(self, line):
        """ Determines whether line is part of a quoted area

            line - a row of the email message

            Returns True or False
        """
        return self.QUOTE_HDR_REGEX.match(line[::-1]) is not None

    def _finish_fragment(self):
        """ Creates fragment
        """

        if self.fragment:
            self.fragment.finish()
            if self.fragment.headers:
                # Regardless of what's been seen to this point, if we encounter a headers fragment,
                # all the previous fragments should be marked hidden and found_visible set to False.
                self.found_visible = False
                for f in self.fragments:
                    f.hidden = True
            if not self.found_visible:
                if self.fragment.quoted \
                        or self.fragment.headers \
                        or self.fragment.signature \
                        or (len(self.fragment.content.strip()) == 0):

                    self.fragment.hidden = True
                else:
                    self.found_visible = True
            self.fragments.append(self.fragment)
        self.fragment = None


class Fragment(object):
    """ A Fragment is a part of
        an Email Message, labeling each part.
    """

    def __init__(self, quoted, first_line, headers=False):
        self.signature = False
        self.headers = headers
        self.hidden = False
        self.quoted = quoted
        self._content = None
        self.lines = [first_line]

    def finish(self):
        """ Creates block of content with lines
            belonging to fragment.
        """
        self.lines.reverse()
        self._content = '\n'.join(self.lines)
        self.lines = None

    @property
    def content(self):
        return self._content.strip()

#TODO move all parsing into here
class SubjectLineParser:
    RE_FW_PATTERN = r'(RE|Re|FW|Fw|:)'
    THREAD_TYPE_CHOICES = MessageThread.ThreadTypes.choices
    JOB_NAMES = [j.name for j in Job.objects.all()]
    
    def __init__(self, subject_line) -> None:
        self.subject_line = subject_line
        self.chosen = {}
        self.best_subject_line_match = {}
        self.min_score_allowed = 50
        self.is_parsed = False
        self.parse()

    def parse(self):
        self.subject_line = re.sub(self.RE_FW_PATTERN, "", self.subject_line).strip()
        self.choose_thread_type()
        self.choose_job_name()
        self.is_parsed = True

    def choose_thread_type(self):
        strings = self.subject_line.split(" ")
        choice = None
        subject_line_match = None
        high_score = 0
        for c in self.THREAD_TYPE_CHOICES:
            ans = process.extractOne(c, strings)
            if ans[1] > high_score:
                high_score = ans[1]
                choice = c
                subject_line_match = ans[0]
        if high_score <= self.min_score_allowed:
            self.chosen['threadType'] = 'Unknown'
        else:
            self.chosen['threadType'] = choice
        self.best_subject_line_match['threadType'] = subject_line_match

    def choose_job_name(self):
        highest_score = 0
        best_choice = None
        best_subject_line_match = None
        string = re.sub(self.best_subject_line_match['threadType'], "", self.subject_line).strip()
        for j in self.JOB_NAMES:
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
            if prev_score > highest_score:
                highest_score = prev_score
                best_choice = j
                best_subject_line_match = prev_subject_line_match

        if highest_score <= self.min_score_allowed:
            self.chosen['jobName'] = 'Unknown'
        else:
            self.chosen['jobName'] = best_choice
        self.best_subject_line_match['jobName'] = best_subject_line_match

    @property
    def thread_type(self):
        assert self.is_parsed
        return self.chosen.get('threadType', 'Unknown')

    @property
    def job_name(self):
        assert self.is_parsed
        return self.chosen.get('jobName', 'Unknown')


class GmailParser:
    pass
