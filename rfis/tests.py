from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model, login, logout
from django.utils import timezone
import json
import base64
import uuid
from http.cookies import SimpleCookie
import random

from google.oauth2.credentials import Credentials

from . import constants as c, email_parser as eparser, models as m, gmail_service, utils as u


def return_random_model_instance(model):
    return random.choice(list(model.objects.all()))

def create_dashboards():
    users = get_user_model().objects.all()
    ret = []
    for u in users:
        dashboard, created =  m.Dashboard.objects.get_or_create(owner=u)
        ret.append(dashboard)
    return ret

def create_threads_w_n_max_messages(n):
    users = get_user_model().objects.all()
    ret = []
    num_msgs = random.randrange(0, n)
    for u in users:
        job = return_random_model_instance(m.Job)
        thread_type = return_random_model_instance(m.MessageThreadType)

        thread, created = m.MessageThread.objects.get_or_create(
            gmail_thread_id=str(uuid.uuid4()),
            job_id=job,
            subject=str(uuid.uuid4()),
            thread_type=thread_type,
            time_received=timezone.now(),
            message_thread_initiator=u,
            accepted_answer=str(uuid.uuid4()),   
        )
        ret.append(thread)
        for _ in range(num_msgs):
            message, mcreated = m.Message.objects.get_or_create(
                message_id=str(uuid.uuid4()),
                message_thread_id=thread,
                subject=str(uuid.uuid4()),
                body=str(uuid.uuid4()),
                to=str(uuid.uuid4()),
                fromm=str(uuid.uuid4()),
                cc=str(uuid.uuid4()),
            )
    return ret

def create_default_db_entries():
    return {
        "users" : {
            "1": get_user_model().objects.get_or_create(email="test@1.com", password="1234"),
            "2": get_user_model().objects.get_or_create(email="test@2.com", password="1234"),
            "3": get_user_model().objects.get_or_create(email="test@3.com", password="1234"),
            "4": get_user_model().objects.get_or_create(email="test@4.com", password="1234"),
            "4": get_user_model().objects.get_or_create(email="test@5.com", password="1234"),
        },
        "jobs" : {
            c.FIELD_VALUE_UNKNOWN_JOB : m.Job.objects.get_or_create(name=c.FIELD_VALUE_UNKNOWN_JOB),
            "Test Job" : m.Job.objects.get_or_create(name="Test Job"),
        },
        "thread_types" : {
            "1" : m.MessageThreadType.objects.get_or_create(name=c.FIELD_VALUE_UNKNOWN_THREAD_TYPE),
            "2" : m.MessageThreadType.objects.get_or_create(name="RFI")
        },
        "dashboards" : create_dashboards(), # list of dashboard objects
        "threads" : create_threads_w_n_max_messages(10), # list of thread objects
    }

def email_password_to_http_auth(email, password):
    return base64.b64encode(bytes(f'{email}:{password}', 'utf8')).decode('utf8')

class EmailParserTestCase(TestCase):
    def setUp(self):
        #self.maxDiff = None
        # any jobs have to be created before the 
        # GmailParser is instantiated
        self.defaults = create_default_db_entries()
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

    def setUp(self):
        self.maxDiff = None
        self.defaults = create_default_db_entries()
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
        self.defaults = create_default_db_entries()
        self.gservice = gmail_service.GmailService()
        self._test_file = open(c.EMAIL_TEST_DATA_PATH, "r+")

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

    def test_get_messages_for_thread(self):
        threads = m.MessageThread.objects.all()
        for thread in threads:
            messages_count = m.Message.objects.filter(message_thread_id=thread).count()
            dashboard = m.Dashboard.objects.get(owner=thread.message_thread_initiator)
            url = reverse("api_get_all_thread_messages", args=[thread.gmail_thread_id])

            # unauthenticated user should get redirected
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

            # owner of the dashboard should be able to see it
            self.client.login(email=dashboard.owner.email, password='1234')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            # form: [{model : name, fields : {fieldname: content} .....]
            data = json.loads(response.json()["data"])
            self.assertEqual(len(list(data)), messages_count)
            self.client.logout()

    #@override_settings(DEBUG="0", USE_SSL="0")
    def test_get_unread_messages_basic_http_auth(self):
        response = self.client.get(reverse("gmail_get_unread_messages"))
        self.assertEqual(response.status_code, 401)

        user = get_user_model().objects.first()
        self.client.defaults['HTTP_AUTHORIZATION'] = f"Basic {email_password_to_http_auth(user.email, '1234')}"
        response = self.client.get(reverse("gmail_get_unread_messages"))
        self.assertEqual(response.status_code, 200)


class MessageManagerTestCase(TestCase):
    client = Client()

    def setUp(self):
        self.maxDiff = None
        self.defaults = create_default_db_entries()

    def test_dashboard_view(self):
        dashboards = m.Dashboard.objects.all()

        for dash in dashboards:
            url = reverse("dashboard_detailed", args=[dash.slug])
            threads = m.MessageThread.objects.filter(message_thread_initiator=dash.owner)

            # unauthenticated user should get redirected
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

            # user who is not a super user or staff or owner of the dashboard
            # should get denied
            user = get_user_model().objects.all().exclude(email=dash.owner.email).first()
            self.client.login(email=user, password='1234')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)
            self.client.logout()

            # owner of the dashboard should be able to see it
            self.client.login(email=dash.owner.email, password='1234')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.client.logout()


