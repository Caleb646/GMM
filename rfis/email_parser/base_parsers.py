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
        if msg_parts := payload.get("parts"):
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
