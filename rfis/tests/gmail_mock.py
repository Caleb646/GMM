import json
import os

from django.conf import settings


class GmailServiceMock:
    test_directory = os.path.join(settings.BASE_DIR, "test_data")
    threads_file = os.path.join(test_directory, "threads.json")
    messages_file = os.path.join(test_directory, "messages.json")

    def __init__(self) -> None:
        self.threads = json.load(open(self.threads_file, "r"))
        self.messages = json.load(open(self.messages_file, "r"))

    def __del__(self):
        pass

    def get_threads(self, query_params=""):
        return [{"id": thread["id"]} for thread in self.threads["threads"]]

    def get_thread(self, thread_id):
        return list(filter(lambda t: t["id"] == thread_id, self.threads["threads"]))[0]

    def get_messages(self, query_params=""):
        return {
            "messages": [
                {"id": msg["id"], "threadId": msg["threadId"]}
                for msg in self.messages["messages"]
            ]
        }

    def get_message(self, message_id):
        return list(
            filter(lambda msg: msg["id"] == message_id, self.messages["messages"])
        )[0]

    def mark_read_messages(self, read_messages):
        return

    def get_attachment(self, message_id, attachment_id):
        return
