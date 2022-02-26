import re
from typing import Dict, List
from thefuzz import process, fuzz
from django.utils import timezone
from email import parser, message as py_email_message, policy
from base64 import urlsafe_b64decode
from bs4 import BeautifulSoup

from .models import MessageThread, Job
from . import utils as u

######################################################################################
# Code was taken from here: https://github.com/zapier/email-reply-parser and modified
######################################################################################
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

################################################################ 
#                       END of zapier code
################################################################

class BaseParser:
    def __init__(self, *args, **kwargs) -> None:
        self._is_parsed = True
        self._chosen = {}

    def parse(self, data):
        raise NotImplementedError

    def _clear(self):
        self._chosen.clear()
        self._is_parsed = False


class BaseBodyParser(BaseParser):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._parts = kwargs.get("parts", False)

    def parse(self, payload):
        self._clear()
        self._chosen["body"] = []
        self._chosen["debug_unparsed_body"] = []
        msg_parts = payload.get("parts")
        if msg_parts:
            self._parse_parts(msg_parts)
        else:
            txt = self._parse_body(payload.get("body", {}).get("data"))
            self._chosen["body"].append(txt)
        self._is_parsed = True
            
    def _parse_body(self, data):
        raise NotImplementedError()

    def _parse_parts(self, data):
        raise NotImplementedError()
    
    @property
    def body(self):
        assert self._is_parsed
        return "".join(self._chosen["body"])

    @property
    def debug_unparsed_body(self):
        assert self._is_parsed
        return "".join(self._chosen["debug_unparsed_body"])


class SubjectLineParser(BaseParser):
    RE_FW_PATTERN = re.compile(r'^(RE|Re|FW|FWD|Fw|):?\s')
    THREAD_TYPE_CHOICES = MessageThread.ThreadTypes.choices
    
    def __init__(self) -> None:
        super().__init__()
        self.JOB_NAMES = [j.name for j in Job.objects.all()]
        self._best_subject_line_match = {}
        self._min_score_allowed = 50

    def parse(self, subject_line):
        self._clear()
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
        strings = self._subject_line.split(" ")
        choice = ""
        subject_line_match = ""
        high_score = 0
        for c, _ in self.THREAD_TYPE_CHOICES:
            ans = process.extractOne(c, strings)
            if ans[1] > high_score:
                high_score = ans[1]
                choice = c
                subject_line_match = ans[0]
        if high_score <= self._min_score_allowed:
            self._chosen['threadType'] = 'Unknown'
        else:
            self._chosen['threadType'] = choice
        self._best_subject_line_match['threadType'] = subject_line_match

    def _choose_job_name(self):
        highest_score = 0
        best_choice = ""
        best_subject_line_match = ""
        cleaned_subject_line = re.sub(self._best_subject_line_match.get('threadType', ""), "", self._subject_line).lower().replace(" ", "")

        cleaned_jobnames_w_actual_jobnames = {j.lower().replace(" ", "") : j for j in self.JOB_NAMES}
        best_match = u.get_best_match(cleaned_jobnames_w_actual_jobnames.keys(), cleaned_subject_line, 0)
        current_string = cleaned_subject_line
        scores = []
        count = 0
        while count < len(cleaned_subject_line):
            current_string = current_string[:-1]
            scores.append(fuzz.ratio(best_match, current_string))
            count += 1
        if max(scores) > self._min_score_allowed:
            self._chosen['jobName'] = cleaned_jobnames_w_actual_jobnames[best_match]
        else:
            self._chosen['jobName'] = 'Unknown'



        # for j in self.JOB_NAMES:
        #     prev_score = 0
        #     prev_subject_line_match = ""

        #     current_score = fuzz.ratio(j, string)   
        #     current_subject_line_match = string

        #     count = len(string)
        #     while current_score > prev_score and count >= 0:
        #         prev_score = current_score
        #         prev_subject_line_match = current_subject_line_match

        #         current_subject_line_match = current_subject_line_match[:-1] #remove last character
        #         current_score = fuzz.ratio(j, current_subject_line_match)

        #         count -= 1
        #     if prev_score > highest_score:
        #         highest_score = prev_score
        #         best_choice = j
        #         best_subject_line_match = prev_subject_line_match
        # if highest_score <= self._min_score_allowed:
        #     self._chosen['jobName'] = 'Unknown'
        # else:
        #     self._chosen['jobName'] = best_choice
        # self._best_subject_line_match['jobName'] = best_subject_line_match

    @property
    def parsed_subject_line(self):
        assert self._is_parsed
        return self._subject_line

    @property
    def thread_type(self):
        assert self._is_parsed
        return self._chosen.get('threadType', 'Unknown')

    @property
    def job_name(self):
        assert self._is_parsed
        return self._chosen.get('jobName', 'Unknown')

class HtmlParser(BaseBodyParser):
    HTML_BODY_PATTERN = re.compile(r'(From|To|RE|FWD|FW|wrote):')

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _parse_body(self, data):
        soup = BeautifulSoup(urlsafe_b64decode(data).decode(), "html.parser")
        #TODO save html to a file
        # https://docs.djangoproject.com/en/4.0/topics/files/
        # with open("output.html", "w") as f:
        #     f.write(str(soup.prettify()))
        self._chosen["debug_unparsed_body"].append(str(soup.prettify())) # store all of the text before the regex is applied for debugging
        text = EmailReplyParser.parse_reply(soup.get_text(" ", strip=True))
        match = re.search(self.HTML_BODY_PATTERN, text)

        #print("\n############ start html text: #####################\n", text, "\n################ end text ###################################\n")
        if match:
            return text[: match.span()[0]]
        return text

    def _parse_parts(self, parts, *args, **kwargs):   
        if not parts:
            return
        for p in parts:
            filename = p.get("filename")
            mimeType = p.get("mimeType")
            body = p.get("body")
            data = body.get("data")
            file_size = body.get("size")
            p_headers = p.get("headers")
            if p.get("parts"):
                self._parse_parts(p.get("parts"))

            if mimeType == "text/html":
                self._chosen['body'].append(self._parse_body(data))


class PlainTextParser(BaseBodyParser):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _parse_body(self, data):
        decoded_data = urlsafe_b64decode(data)
        self._chosen["debug_unparsed_body"].append(decoded_data.decode()) # store all of the text before the regex is applied for debugging
        email_message = parser.BytesParser(_class=py_email_message.EmailMessage, policy=policy.default).parsebytes(decoded_data)

        #print("\n################## start raw text: ##########################\n", email_message, "\n######################### end raw text ##############################\n")
        return EmailReplyParser.parse_reply(str(email_message.get_body()))

    def _parse_parts(self, parts):   
        if not parts:
            return
        for p in parts:
            filename = p.get("filename")
            mimeType = p.get("mimeType")
            body = p.get("body")
            data = body.get("data")
            file_size = body.get("size")
            p_headers = p.get("headers")
            if p.get("parts"):
                self._parse_parts(p.get("parts"))

            if mimeType == "text/plain" and data:            
                self._chosen['body'].append(self._parse_body(data))



class GmailParser(BaseParser):
    EMAIL_ADDRESS_PATTERN = re.compile(r'([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)')
    BODY_PARSERS_XMAILER = {
        "iPhone Mail": {
            "text/plain": PlainTextParser(),
            "text/html": HtmlParser(),        
            "multipart/alternative": HtmlParser(parts=True),
            "multipart/mixed": HtmlParser(),
            },
        "default":{
            "text/plain": PlainTextParser(),
            "text/html": HtmlParser(),        
            "multipart/alternative": HtmlParser(parts=True),
            "multipart/mixed": HtmlParser(), 
            }
    }
    def __init__(self) -> None:
        super().__init__()
        self._subject_parser = SubjectLineParser()


    def parse(self, gmail_message):
        self._clear()
        if not gmail_message:
            return
        self._chosen["message_id"] = gmail_message["id"]
        self._chosen["thread_id"] = gmail_message["threadId"]
        payload = gmail_message.get("payload")
        #print("\npayload: ", payload, "\n")
        assert payload, "Payload cannot be None"
        # set mime type for later use
        self._chosen["mime_type"] = payload.get("mimeType")
        # headers have to be parsed for the body parser to be picked
        self._parse_headers(payload.get("headers"))
        # pick body parser
        self._body_parser = self._choose_body_parser()
        self._body_parser.parse(payload)
        
        self._subject_parser.parse(self._chosen["headers"]["Subject"])
        self._is_parsed = True

    def format_test_data(self, character_to_replace=" "):
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "mime_type": self.mime_type,
            "x_mailer": self.x_mailer,
            "body": self.body.replace(character_to_replace, ""),
            "Subject": self.subject.replace(character_to_replace, ""),
            "From": self.fromm.replace(character_to_replace, ""),
            "To": self.to.replace(character_to_replace, ""),
            "Cc": self.cc.replace(character_to_replace, ""),
            "Date": self.date.replace(character_to_replace, ""),
            "thread_type": self.thread_type.replace(character_to_replace, ""),
            "job_name": self.job_name.replace(character_to_replace, "")
        }

    def _choose_body_parser(self):
        xmail_header = self._chosen['headers']["x_mailer"]
        mime_type = self._chosen["mime_type"]
        if not xmail_header:
            return self.BODY_PARSERS_XMAILER["default"].get(mime_type, HtmlParser(parts=True))
        chosen_xmailer = self._chosen['headers']["x_mailer"] = u.get_best_match(self.BODY_PARSERS_XMAILER.keys(), xmail_header)
        chosen_xmailer_parser: Dict[str : BaseBodyParser] = self.BODY_PARSERS_XMAILER.get(chosen_xmailer, self.BODY_PARSERS_XMAILER["default"])
        return chosen_xmailer_parser.get(mime_type, HtmlParser(parts=True))

    def _parse_headers(self, headers, *args, **kwargs):
        self._chosen['headers'] = {
            "Subject": "Unknown",
            "From": "Unknown",
            "To": "Unknown",
            "Date": f"{timezone.now()}",
            "x_mailer": "Unknown"
        }
        if not headers:
            return 
        for h in headers:
            head = h.get("name")
            value = h.get("value")
            if head == "Subject":
                self._chosen['headers']["Subject"] = value
            elif head == "From":
                self._chosen['headers']["From"] = self._parse_email_address(value)[0]
            elif head == "To":
                self._chosen['headers']["To"] = " ".join(self._parse_email_address(value))
            elif head == "Cc":
                self._chosen['headers']["Cc"] = " ".join(self._parse_email_address(value))
            elif head == "Date":
                self._chosen['headers']["Date"] = value
            elif head == "X-Mailer":
                self._chosen['headers']["x_mailer"] = value

    def _parse_email_address(self, email_string: str):
        address_or_addresses: List[str] = re.findall(self.EMAIL_ADDRESS_PATTERN, email_string)
        if len(address_or_addresses) == 0:
            return [""]
        return list(set(address_or_addresses))

    @property
    def message_id(self):
        assert self._is_parsed
        return self._chosen["message_id"]

    @property
    def thread_id(self):
        assert self._is_parsed
        return self._chosen["thread_id"]

    @property
    def mime_type(self):
        assert self._is_parsed
        return self._chosen["mime_type"]

    @property
    def body(self):
        assert self._is_parsed
        return "".join(self._body_parser.body)

    @property
    def debug_unparsed_body(self):
        assert self._is_parsed
        return "".join(self._body_parser.debug_unparsed_body)

    @property
    def headers(self):
        assert self._is_parsed
        return self._chosen["headers"]

    @property
    def subject(self):
        assert self._is_parsed
        return self._subject_parser.parsed_subject_line

    @property
    def fromm(self):
        assert self._is_parsed
        return self._chosen["headers"]["From"]

    @property
    def to(self):
        assert self._is_parsed
        return self._chosen["headers"]["To"]

    @property
    def cc(self):
        assert self._is_parsed
        return self._chosen["headers"].get("Cc", "")
       
    @property
    def date(self):
        assert self._is_parsed
        return self._chosen["headers"]["Date"]

    @property
    def x_mailer(self):
        assert self._is_parsed
        return self._chosen["headers"]["x_mailer"]

    @property
    def thread_type(self):
        assert self._is_parsed
        return self._subject_parser.thread_type

    @property
    def job_name(self):
        assert self._is_parsed
        return self._subject_parser.job_name