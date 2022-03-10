from django.test import TestCase, Client, override_settings
from django.urls import reverse, reverse_lazy
from django.contrib.auth import get_user_model
from django.utils import timezone
from urllib.parse import urljoin
import json
import base64
import uuid
from http.cookies import SimpleCookie
import random

from google.oauth2.credentials import Credentials

from . import constants as c, email_parser as eparser, models as m, gmail_service, utils as u

PASSWORD = '1234'
ADMIN_LOGIN = reverse_lazy("admin:login")
USER_LOGIN = reverse_lazy("base_user_login")
client = Client()

def email_password_to_http_auth(email):
    return base64.b64encode(bytes(f'{email}:{PASSWORD}', 'utf8')).decode('utf8')

def auth_check(url, email, status_code):   
    client.login(email=email, password=PASSWORD)
    response = client.get(url, follow=True)
    client.logout()
    if response.redirect_chain:
        assert any(status_code in route for route in response.redirect_chain), f"Redirect chain {response.redirect_chain} != Target code: {status_code} on {url}"  
    else:
        assert response.status_code == status_code, f"Response code {response.status_code} != Target code: {status_code} on {url}"  
    return response

def basic_auth_check(url, email, status_code):
    client.defaults['HTTP_AUTHORIZATION'] = f"Basic {email_password_to_http_auth(email)}"
    response = client.get(url, follow=True)
    client.defaults['HTTP_AUTHORIZATION'] = SimpleCookie()
    assert response.status_code == status_code, f"Response code {response.status_code} != Target code: {status_code} on {url}"

def redirect_join(to, fromm):
    return urljoin(str(to), f"?next={str(fromm)}")

def redirect_auth_check(url, email, status_code, redirect_url):
    response = auth_check(url, email, status_code)
    found = any(redirect_url in route for route in response.redirect_chain)
    assert found, f"Target Redirect: {redirect_url} not in Redirect Chain: {response.redirect_chain}"


def return_random_model_instance(model):
    return random.choice(list(model.objects.all()))

def create_dashboards():
    users = get_user_model().objects.all()
    ret = []
    for u in users:
        dashboard, created =  m.MessageLog.objects.get_or_create(owner=u)
        ret.append(dashboard)
    return ret

def create_threads_w_n_max_messages(n):
    users = get_user_model().objects.all()
    ret = []
    num_msgs = random.randrange(0, n)
    for u in users:
        job = return_random_model_instance(m.Job)
        thread_type = return_random_model_instance(m.ThreadType)

        thread, created = m.Thread.objects.get_or_create(
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
            "1": get_user_model().objects.get_or_create(email="test1", password=PASSWORD),
            "2": get_user_model().objects.get_or_create(email="test2", password=PASSWORD),
            "3": get_user_model().objects.get_or_create(email="test3", password=PASSWORD),
            "4": get_user_model().objects.get_or_create(email="test4", password=PASSWORD),
            "4": get_user_model().objects.get_or_create(email="test5", password=PASSWORD),
            "staff": get_user_model().objects.get_or_create(email="staff", password=PASSWORD, is_staff=True),
            "admin": get_user_model().objects.get_or_create(
                email="admin", 
                password=PASSWORD,
                is_staff=True,
                is_superuser=True
                ),
        },
        "jobs" : {
            c.FIELD_VALUE_UNKNOWN_JOB : m.Job.objects.get_or_create(name=c.FIELD_VALUE_UNKNOWN_JOB),
            "Test Job" : m.Job.objects.get_or_create(name="Test Job"),
        },
        "thread_types" : {
            "1" : m.ThreadType.objects.get_or_create(name=c.FIELD_VALUE_UNKNOWN_THREAD_TYPE),
            "2" : m.ThreadType.objects.get_or_create(name="RFI")
        },
        "dashboards" : create_dashboards(), # list of dashboard objects
        "threads" : create_threads_w_n_max_messages(10), # list of thread objects
    }

class EmailParserTestCase(TestCase):
    # def setUp(self):
    #     #self.maxDiff = None
    #     # any jobs have to be created before the 
    #     # GmailParser is instantiated
    #     self.defaults = create_default_db_entries()
    #     self._test_file = open(c.EMAIL_TEST_DATA_PATH, "r+")
    #     self._parser = eparser.GmailParser()

    @classmethod
    def setUpTestData(cls):
        cls.defaults = create_default_db_entries()
        cls._test_file = open(c.EMAIL_TEST_DATA_PATH, "r+")
        cls._parser = eparser.GmailParser()

    @classmethod
    def tearDownClass(cls):
        cls._test_file.close()
        super().tearDownClass()

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

    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = create_default_db_entries()
        cls.gservice = gmail_service.GmailService()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

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

    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = create_default_db_entries()
        cls.gservice = gmail_service.GmailService()
        cls._test_file = open(c.EMAIL_TEST_DATA_PATH, "r+")

    @classmethod
    def tearDownClass(cls):
        cls._test_file.close()
        super().tearDownClass()

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
        threads = m.Thread.objects.all()
        for thread in threads:
            messages_count = m.Message.objects.filter(message_thread_id=thread).count()
            dashboard = m.MessageLog.objects.get(owner=thread.message_thread_initiator)
            url = reverse("api_get_all_thread_messages", args=[thread.gmail_thread_id])

            # unauthenticated user should get redirected
            redirect_auth_check(url, "", 302, redirect_join(USER_LOGIN, url))
            auth_check(url, "staff", 200)
            auth_check(url, "admin", 200)
            # owner of the dashboard should be able to see it
            response = auth_check(url, dashboard.owner.email, 200)
            # form: [{model : name, fields : {fieldname: content} .....]
            data = json.loads(response.json()["data"])
            self.assertEqual(len(list(data)), messages_count)

    #@override_settings(DEBUG="0", USE_SSL="0")
    def test_get_unread_messages_basic_http_auth(self):
        url = reverse("gmail_get_unread_messages")
        auth_check(url, "", 401)
        user = get_user_model().objects.first()
        basic_auth_check(url, user.email, 200)

class MessageManagerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = create_default_db_entries()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_dashboard_view(self):
        dashboards = m.MessageLog.objects.all()
        for dash in dashboards:
            url = reverse("dashboard_detailed", args=[dash.slug])
            threads = m.Thread.objects.filter(message_thread_initiator=dash.owner)

            # unauthenticated user should get redirected
            redirect_auth_check(url, "", 302, redirect_join(USER_LOGIN, url))

            # user who is not a super user or staff or owner of the dashboard
            # should get denied
            user = get_user_model().objects.all().exclude(email=dash.owner.email).first()
            auth_check(url, user.email, 403)

            auth_check(url, "staff", 200)
            auth_check(url, "admin", 200)
            # owner of the dashboard should be able to see it
            auth_check(url, dash.owner.email, 200)



class AdminTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.defaults = create_default_db_entries()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_thread_detailed(self):
        threads = m.Thread.objects.all()
        for thread in threads:
            url = reverse('admin:message_thread_detailed_view', args=[thread.id])

            # unauthenticated user should get redirected
            redirect_auth_check(url, "", 302, redirect_join(ADMIN_LOGIN, url))
            auth_check(url, "test1", 403)
            auth_check(url, "staff", 200)
            response = auth_check(url, "admin", 200)
            # https://docs.djangoproject.com/en/4.0/topics/testing/tools/
            # context is a list of contexts
            context = response.context
            #print(response.context)
            


