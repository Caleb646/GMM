from django.test import TestCase, Client, override_settings
import json

from app.app.settings.settings import USE_SSL

from . import constants as c, email_parser as eparser, models as m, gmail_service

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
        
            self.assertDictEqual(tested, answer, f"\n\nTest: {tested}\n\nAnswer: {answer}")


class GmailServiceTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.gservice = gmail_service.GmailService()

    @override_settings(DEBUG="0", USE_SSL="0") # set debug to false to use AWS S3 storage
    def test_save_load_tokens_credentials(self):
        pass

    #TODO need to test gmail api methods. Instead of test the views themselves just test the methods that
    # make up the views. 
    # 1. Test save and load client config and client tokens
    # 2. Test getting a single message and thread
    # 3. Test refresh decorator
    # 4. Tests need to be run in production env as well w/ AWS S3 storage
