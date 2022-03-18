import re
from typing import List

from .base_parsers import BaseParser
from .content_parsers import MultiPartParser
from .subjectline_parser import SubjectLineParser


class GmailParser(BaseParser):
    EMAIL_ADDRESS_PATTERN = re.compile(
        r"([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)"
    )

    def __init__(self) -> None:
        super().__init__()
        self._subject_parser = SubjectLineParser()

    def parse(self, gmail_message):
        self._clear()
        if not gmail_message:
            return
        self._chosen["message_id"] = gmail_message["id"]
        self._chosen["thread_id"] = gmail_message["threadId"]
        self._chosen["headers"] = {
            "Subject": "Unknown",
            "From": "Unknown",
            "To": "Unknown",
            # internalDate is more accurate than Date header
            "Date": gmail_message["internalDate"],
            "x_mailer": "Unknown",
        }
        payload = gmail_message.get("payload")
        # print("\npayload: ", payload, "\n")
        assert payload, "Payload cannot be None"
        # set mime type for later use
        self._chosen["mime_type"] = payload.get("mimeType")
        # headers have to be parsed for the body parser to be picked
        self._parse_headers(payload.get("headers"))
        self._body_parser = MultiPartParser(prefer_html=False)
        self._body_parser.parse(payload)

        self._subject_parser.parse(self._chosen["headers"]["Subject"])
        self._is_parsed = True

    def format_test_data(self, character_to_replace=" "):
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "mime_type": self.mime_type,
            "x_mailer": "Unknown",
            "body": self.body.replace(character_to_replace, ""),
            "Subject": self.subject.replace(character_to_replace, ""),
            "From": self.fromm.replace(character_to_replace, ""),
            "To": self.to.replace(character_to_replace, ""),
            "Cc": self.cc.replace(character_to_replace, ""),
            "Date": self.date.replace(character_to_replace, ""),
            "thread_type": self.thread_type.replace(character_to_replace, ""),
            "job_name": self.job_name.replace(character_to_replace, ""),
            "files_info": self.files_info,
        }

    def _parse_headers(self, headers, *args, **kwargs):
        if not headers:
            return
        for h in headers:
            head = h.get("name")
            value = h.get("value")
            if head == "Subject":
                self._chosen["headers"]["Subject"] = value
            elif head == "From":
                self._chosen["headers"]["From"] = self._parse_email_address(value)[0]
            elif head == "To":
                self._chosen["headers"]["To"] = " ".join(self._parse_email_address(value))
            elif head == "Cc":
                self._chosen["headers"]["Cc"] = " ".join(self._parse_email_address(value))
            elif head == "X-Mailer":
                self._chosen["headers"]["x_mailer"] = value

    def _parse_email_address(self, email_string: str):
        address_or_addresses: List[str] = re.findall(
            self.EMAIL_ADDRESS_PATTERN, email_string
        )
        if not address_or_addresses:
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
    def files_info(self):
        assert self._is_parsed
        if isinstance(self._body_parser, MultiPartParser):
            return self._body_parser.files_info
        return []

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
