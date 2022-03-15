import base64
import itertools
import json
import math
import os
from typing import List, Optional, Tuple

import dateparser
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Permission
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import HttpResponse
from storages.backends.s3boto3 import S3Boto3Storage, S3Boto3StorageFile
from thefuzz import fuzz, process

from . import models as m


def load_file(path, transform_file=lambda f: f, mode="rb"):
    head, tail = os.path.split(path)
    assert default_storage.exists(name=tail), f"filename: {tail}"
    if isinstance(default_storage, S3Boto3Storage):
        file: S3Boto3StorageFile = default_storage.open(tail, mode)
        data = transform_file(file)
        file.close()
        return data
    return transform_file(default_storage.open(tail, mode))


def should_create_thread(gmail_thread_id, from_email):
    """
    Cases:
        User exist but the Thread does not -> True
        User doesnt exist but the Thread does -> True
        Both User and the Thread do exist -> True
        Both User and the Thread do not exist -> False
    """
    # TODO if user doesnt exist dont accept a message from them. May need to add a setting for this
    return bool(
        get_user_model().objects.filter(email=from_email).exists()
        or m.Thread.objects.filter(gmail_thread_id=gmail_thread_id).exists()
    )


def create_db_entry_from_parser(
    g_parser: "rfis.email_parser.GmailParser", gmail_message
) -> bool:
    g_parser.parse(gmail_message)
    if not should_create_thread(g_parser.thread_id, g_parser.fromm):
        return False
    time_message_received = dateparser.parse(
        g_parser.date,
        settings={
            "TO_TIMEZONE": settings.TIME_ZONE,
            "RETURN_AS_TIMEZONE_AWARE": True,
        },
    )
    print(time_message_received)
    # neither of these two should be created at this point
    job = m.Job.objects.get(name=g_parser.job_name)
    message_type = m.ThreadType.objects.get(name=g_parser.thread_type)
    # The user may not exist because they were not the ones who sent
    # the very first message, but a thread will never be created without a user
    user: Optional[m.MyUser] = (
        get_user_model().objects.filter(email=g_parser.fromm).first()
    )

    message_thread, mtcreated = m.Thread.objects.get_or_create(
        gmail_thread_id=g_parser.thread_id,
        job_id=job,
        thread_type=message_type,
        time_received=time_message_received,
        subject=g_parser.subject,
        message_thread_initiator=user,
    )
    message, mcreated = m.Message.objects.get_or_create(
        message_id=g_parser.message_id,
        message_thread_id=message_thread,
        subject=g_parser.subject,
        body=g_parser.body,
        debug_unparsed_body=g_parser.debug_unparsed_body,
        fromm=g_parser.fromm,
        to=g_parser.to,
        cc=g_parser.cc,
        time_received=time_message_received,
    )
    for f_info in g_parser.files_info:
        attachment, created = m.Attachment.objects.get_or_create(
            filename=f_info["filename"],
            gmail_attachment_id=f_info["gmail_attachment_id"],
            time_received=time_message_received,
            message_id=message,
        )
    return True


def find_earliest_message_index(messages):
    earliest_message_index = 0
    earliest_message_time = math.inf
    for i, msg in enumerate(messages):
        msg_date = int(msg["internalDate"])
        if msg_date < earliest_message_time:
            earliest_message_time = msg_date
            earliest_message_index = i
    return earliest_message_index


def process_single_gmail_thread(messages, g_parser):
    read_messages = []
    if not messages:
        return read_messages
    earliest_message_index = find_earliest_message_index(messages)
    # set the earliest message as the first message in the list
    # so the message_thread_initiator field will be set correctly
    if earliest_message_index != len(messages):
        earliest_message = messages[earliest_message_index]
        first_message = messages[0]
        earliest_message, first_message = first_message, earliest_message
    for msg in messages:
        created = create_db_entry_from_parser(g_parser, msg)
        if created:
            read_messages.append(g_parser.message_id)
    return read_messages


def process_multiple_gmail_threads(
    service, g_parser, query_params="label:inbox is:unread"
):
    unread_threads = service.get_threads(query_params)
    read_messages: list[list[int]] = []
    for thread_info in unread_threads:
        thread = service.get_thread(thread_info["id"])
        read_messages.append(
            process_single_gmail_thread(thread.get("messages"), g_parser)
        )

    return list(itertools.chain(*read_messages))


def get_permission_object(permission_str):  # rfis.view_message
    app_label, codename = permission_str.split(".")
    perm = Permission.objects.filter(
        content_type__app_label=app_label, codename=codename
    ).first()
    assert perm, "Permission cannot be none"
    return perm


def get_users_with_permission(permission_str, include_su=True):
    permission_obj = get_permission_object(permission_str)
    q = Q(groups__permissions=permission_obj) | Q(user_permissions=permission_obj)
    if include_su:
        q |= Q(is_superuser=True)
    return get_user_model().objects.filter(q).distinct()


def get_best_match(
    queries: List[str], choices: List[str], string_processor=lambda x: x
) -> Tuple[str, str, int]:
    assert isinstance(queries, list)
    assert isinstance(choices, list)
    picks = []
    for c in queries:
        ans = process.extractOne(string_processor(c), choices, processor=string_processor)
        picks.append([c, ans[0], ans[1]])
    # print(f"\nqueries: {queries} best match: {max(picks, key=lambda x : x[2])} to_match: {choices}\n")
    if picks:
        return max(picks, key=lambda x: x[2])
    return ["", "", 0]


def get_highest_possible_match(
    match: str, to_match: str, string_processor=lambda x: x
) -> int:
    assert isinstance(match, str)
    assert isinstance(to_match, str)
    un_modified_match = match
    to_match = string_processor(to_match)
    match = string_processor(match)
    scores = []
    for _ in range(len(to_match)):
        to_match = to_match[:-1]
        scores.append(fuzz.ratio(match, to_match))
    # print(f"\nun_modified_match: {un_modified_match} to_match: {to_match} scores: {scores}\n")
    return un_modified_match, max(scores)


def save_test_data_from_raw_gmail_message(raw_gmail_message, parsed_message, filename):
    data = {"raw_gmail_message": raw_gmail_message, "parsed_message": parsed_message}

    with open(filename, "r+") as file:
        file_data = json.load(file)
        file_data["test_messages"].append(data)
        file.seek(0)
        json.dump(file_data, file, indent=4)


###############################################################################################
#           Taken from https://www.djangosnippets.org/snippets/243/ and modified
###############################################################################################


def view_or_basicauth(view, request, test_func, realm="", *args, **kwargs):
    """
    This is a helper function used by both 'logged_in_or_basicauth' and
    'has_perm_or_basicauth' that does the nitty of determining if they
    are already logged in or if they have provided proper http-authorization
    and returning the view if all goes well, otherwise responding with a 401.
    """
    if test_func(request.user):
        # Already logged in, just return the view.
        #
        return view(request, *args, **kwargs)

    # They are not logged in. See if they provided login credentials
    #
    if "HTTP_AUTHORIZATION" in request.META:
        auth = request.META["HTTP_AUTHORIZATION"].split()
        if len(auth) == 2:
            # NOTE: We are only support basic authentication for now.
            #
            if auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).decode().split(":")
                user = authenticate(username=uname, password=passwd)
                if user is not None:
                    if user.is_active:
                        # Don't want to log a Http Authorization user in.
                        # They should have to reauthenticate on every request.
                        # External apis should be the only ones using Http Authorization
                        # for authentication.
                        # login(request, user)
                        request.user = user
                        return view(request, *args, **kwargs)

    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    #
    response = HttpResponse()
    response.status_code = 401
    response["WWW-Authenticate"] = 'Basic realm="%s"' % realm
    return response


#############################################################################
#


def logged_in_or_basicauth(realm=""):
    """
    A simple decorator that requires a user to be logged in. If they are not
    logged in the request is examined for a 'authorization' header.

    If the header is present it is tested for basic authentication and
    the user is logged in with the provided credentials.

    If the header is not present a http 401 is sent back to the
    requestor to provide credentials.

    The purpose of this is that in several django projects I have needed
    several specific views that need to support basic authentication, yet the
    web site as a whole used django's provided authentication.

    The uses for this are for urls that are access programmatically such as
    by rss feed readers, yet the view requires a user to be logged in. Many rss
    readers support supplying the authentication credentials via http basic
    auth (and they do NOT support a redirect to a form where they post a
    username/password.)

    Use is simple:

    @logged_in_or_basicauth()
    def your_view:
        ...

    You can provide the name of the realm to ask for authentication within.
    """

    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(
                func, request, lambda u: u.is_authenticated, realm, *args, **kwargs
            )

        return wrapper

    return view_decorator


#############################################################################
#
def has_perm_or_basicauth(perm, realm=""):
    """
    This is similar to the above decorator 'logged_in_or_basicauth'
    except that it requires the logged in user to have a specific
    permission.

    Use:

    @logged_in_or_basicauth('asforums.view_forumcollection')
    def your_view:
        ...

    """

    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(
                func, request, lambda u: u.has_perm(perm), realm, *args, **kwargs
            )

        return wrapper

    return view_decorator


###############################################################################################
#           END https://www.djangosnippets.org/snippets/243/
###############################################################################################
