from django.test import TestCase, Client, override_settings
from django.urls import reverse
import json
import base64

from google.oauth2.credentials import Credentials

from . import constants as c, email_parser as eparser, models as m, gmail_service, utils as u

class EmailParserTestCase(TestCase):
    def setUp(self):
        #self.maxDiff = None
        # any jobs have to be created before the 
        # GmailParser is instantiated
        m.Job.objects.get_or_create(name="Test Job")
        m.MessageThreadType.objects.get_or_create(name="RFI")
        m.MessageThreadType.objects.get_or_create(name=c.FIELD_VALUE_UNKNOWN_THREAD_TYPE)

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
        
            self.assertDictEqual(tested, answer)#,f"\n\nTest: {tested}\n\nAnswer: {answer}")


class GmailServiceTestCase(TestCase):
    client = Client()
    m.Job.objects.get_or_create(name="Test Job")
    m.MessageThreadType.objects.get_or_create(name="RFI")
    m.MessageThreadType.objects.get_or_create(name=c.FIELD_VALUE_UNKNOWN_THREAD_TYPE)

    def setUp(self):
        self.maxDiff = None
        self.gservice = gmail_service.GmailService()

    #@override_settings(DEBUG="0", USE_SSL="0") # set debug to false to use AWS S3 storage
    def test_save_load_tokens_credentials(self):
        client_config = gmail_service.GmailService.load_client_secret_config_f_file()
        #test that client id is there
        client_config["web"]["client_id"]

        #test that token and refresh token
        token = gmail_service.GmailService.load_client_token()
        token["token"]
        token["refresh_token"]

        #test saving credentials
        creds = Credentials.from_authorized_user_info(gmail_service.GmailService.load_client_token(), c.GMAIL_API_SCOPES)
        gmail_service.GmailService.save_client_token(creds)

    # will test refresh decorator as well
    #@override_settings(DEBUG="0", USE_SSL="0")
    def test_get_message_thread(self):
        service = gmail_service.GmailService()
        threads = service.get_threads("label:inbox")
        assert len(threads) > 0
        thread = service.get_thread(threads[0]["id"])
        assert thread
        assert thread["messages"]
        message = service.get_message(thread["messages"][0]["id"])
        assert message


class ApiTestCase(TestCase):
    client = Client()

    def setUp(self):
        self.maxDiff = None
        self.gservice = gmail_service.GmailService()
        self._test_file = open(c.EMAIL_TEST_DATA_PATH, "r+")

        m.MyUser.objects.get_or_create(email="test@test.com", password="1234")
        m.Job.objects.get_or_create(name=c.FIELD_VALUE_UNKNOWN_JOB)
        m.Job.objects.get_or_create(name="Test Job")
        m.MessageThreadType.objects.get_or_create(name="RFI")
        m.MessageThreadType.objects.get_or_create(name=c.FIELD_VALUE_UNKNOWN_THREAD_TYPE)

    def tearDown(self) -> None:
        self._test_file.close()
        return super().tearDown()

    def test_create_db_entry_from_parser(self):
        _parser = eparser.GmailParser()
        parsed_message_ids = []
        data = json.load(self._test_file)
        for msg in data["test_messages"]:
            created = u.create_db_entry_from_parser(_parser, msg["raw_gmail_message"], create_from_any_user=True) 
            parsed_message_ids.append(_parser.message_id)

        for message_id in parsed_message_ids:
            m.Message.objects.get(message_id=message_id)


    #@override_settings(DEBUG="0", USE_SSL="0")
    def test_get_unread_messages_basic_http_auth(self):
        response = self.client.get(reverse("gmail_get_unread_messages"))
        self.assertEqual(response.status_code, 401)

        credentials = base64.b64encode(bytes('test@test.com:1234', 'utf8')).decode('utf8')
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Basic {credentials}'
        response = self.client.get(reverse("gmail_get_unread_messages"))
        self.assertEqual(response.status_code, 200)
