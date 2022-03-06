from django.test import TestCase
import json

from . import constants as c, email_parser as eparser, models as m

class EmailParserTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        # any jobs have to be created before the 
        # GmailParser is instantiated
        m.Job.objects.create(name="Test Job")

        self._test_file = open(c.EMAIL_TEST_DATA_PATH, "r+")
        self._parser = eparser.GmailParser()

    def tearDown(self) -> None:
        self._test_file.close()
        return super().tearDown()

    def test_email_parser(self):
        data = json.load(self._test_file)
        for msg in data["test_messages"]:
            self._parser.parse(msg["raw_gmail_message"])

            answer = msg["parsed_message"]   
            tested = self._parser.format_test_data()

            # Because part of the email address parsing uses a 
            # set to remove duplicates the order is sometimes not the same.
            # This fixes that and makes them comparable.
            answer["To"] = sorted(answer["To"])
            tested["To"] = sorted(tested["To"])
        
            self.assertDictEqual(tested, answer, f"\n\ntest: {tested}\n\nanswer: {answer}")
