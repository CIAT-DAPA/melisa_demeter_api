
import re

class RequestMelisa():

    # Method construct
    def __init__(self, data, files):
        self.melisa_name = data["melisa"]
        self.melisa_token = data["token"]
        self.user_id = data["user"]
        self.message_raw = data["message"]
        self.kind = data["kind"] if "kind" in data else "text"
        self.chat_id = data["chat_id"] if "chat_id" in data else ""
        self.user_tags = data["user_tags"]  if "user_tags" in data else {}
        self.message_tags = data["message_tags"] if "message_tags" in data else {}
        self.message_normalized = ""
        self.files = files

    # Method that validate the mandatory fields for the request
    def validate_request(self):
        if not self.melisa_name or not self.melisa_name.strip():
            raise ValueError("Melisa name is empty")
        else:
            self.melisa_name = self.melisa_name.strip()

        if not self.melisa_token or not self.melisa_token.strip():
            raise ValueError("Melisa token is empty")
        else:
            self.melisa_token = self.melisa_token.strip()

        if not self.user_id or not self.user_id.strip():
            raise ValueError("User id is empty")
        else:
            self.user_id = self.user_id.strip()

        if self.kind == "text" and not self.message_raw or not self.message_raw.strip():
            raise ValueError("Message is empty")
        else:
            self.message_normalized = self.message_raw.strip().replace("_"," ")

        if self.kind != "text" and len(self.files) == 0:
            raise ValueError("File is empty")
