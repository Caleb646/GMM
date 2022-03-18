import re
from base64 import urlsafe_b64decode

from bs4 import BeautifulSoup

from .base_parsers import BaseBodyParser
from .reply_parser import EmailReplyParser


class HtmlParser(BaseBodyParser):
    HTML_BODY_PATTERN = re.compile(r"(From|To|RE|FWD|FW|wrote):")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _parse_body(self, data):
        soup = BeautifulSoup(urlsafe_b64decode(data).decode(), "html.parser")
        self._chosen["debug_unparsed_body"].append(
            str(soup.prettify())
        )  # store all of the text before the regex is applied for debugging
        # text = EmailReplyParser.parse_reply(soup.get_text(" ", strip=True))
        text = soup.get_text(" ", strip=True)
        if match := re.search(self.HTML_BODY_PATTERN, text):
            return text[: match.span()[0]]
        return text

    def _parse_parts(self, parts):
        assert parts, f"Parts cannot be {parts}"
        for p in parts:
            mimeType = p.get("mimeType")
            body = p.get("body")
            data = body.get("data")
            if p.get("parts"):
                self._parse_parts(p.get("parts"))

            if mimeType == "text/html":
                self._chosen["body"].append(self._parse_body(data))


class PlainTextParser(BaseBodyParser):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _parse_body(self, data):
        decoded_data = urlsafe_b64decode(data).decode()

        soup = BeautifulSoup(decoded_data, "html.parser")
        text = soup.get_text(" ", strip=True)

        # print(
        #     "\n################## start decoded_data text: ##########################\n",
        #     text,
        #     "\n######################### end decoded_data text"
        #     " ##############################\n",
        # )

        self._chosen["debug_unparsed_body"].append(
            text
        )  # store all of the text before the regex is applied for debugging
        return EmailReplyParser.parse_reply(text)

    def _parse_parts(self, parts):
        assert parts, f"Parts cannot be {parts}"
        for p in parts:
            mimeType = p.get("mimeType")
            body = p.get("body")
            data = body.get("data")
            if p.get("parts"):
                self._parse_parts(p.get("parts"))

            if mimeType == "text/plain" and data:
                self._chosen["body"].append(self._parse_body(data))


class MultiPartParser(BaseBodyParser):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._prefer_html = kwargs.get("prefer_html", True)
        self._are_attachments = kwargs.get("are_attachments", False)
        self._html_parser = HtmlParser()
        self._text_parser = PlainTextParser()

    def parse(self, payload):
        self._clear()
        self._chosen["body"] = []
        self._chosen["debug_unparsed_body"] = []
        self._chosen["files_info"] = []
        self._html_parser.parse(payload)
        self._text_parser.parse(payload)
        if message_parts := payload.get("parts"):
            self._parse_attachments(message_parts)
        self._is_parsed = True

    def _parse_attachments(self, parts):
        assert parts, f"Parts cannot be {parts}"
        for p in parts:
            filename = p.get("filename")
            attachment_id = p.get("body", {}).get("attachmentId")
            mimeType = p.get("mimeType")
            body = p.get("body")
            data = body.get("data")
            file_size = body.get("size")
            p_headers = p.get("headers")
            if p.get("parts"):
                self._parse_attachments(p.get("parts"))
            if filename != "" and attachment_id:
                self._chosen["files_info"].append(
                    {"filename": filename, "gmail_attachment_id": attachment_id}
                )

    @property
    def body(self):
        assert self._is_parsed
        if self._prefer_html and self._html_parser.body:
            return self._html_parser.body
        elif self._text_parser.body:
            return self._text_parser.body
        else:
            return self._text_parser.body + self._html_parser.body

    @property
    def debug_unparsed_body(self):
        assert self._is_parsed
        if self._prefer_html and self._html_parser.debug_unparsed_body:
            return self._html_parser.debug_unparsed_body
        elif self._text_parser.debug_unparsed_body:
            return self._text_parser.debug_unparsed_body
        else:
            return (
                self._text_parser.debug_unparsed_body
                + self._html_parser.debug_unparsed_body
            )

    @property
    def files_info(self):
        assert self._is_parsed
        return self._chosen["files_info"]
