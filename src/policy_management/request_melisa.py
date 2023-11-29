
import re

class RequestMelisa():

    # Method construct
    def __init__(self, data):
        self.melisa_name = data["melisa"]
        self.melisa_token = data["token"]
        self.user_id = data["user"]
        self.message = data["message"]
        self.chat_id = data["chat_id"] if "chat_id" in  data else ""
        self.user_tags = data["user_tags"]  if "user_tags" in data else {}
        self.message_tags = data["message_tags"] if "message_tags" in data else {}
        pass

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

        if not self.message or not self.message.strip():
            raise ValueError("Message is empty")
        else:
            self.message = self.message.strip().replace("_"," ")
            self.statements = self.split_message_statements(self.message)

    def split_message_statements(self,text):
        # Creamos una expresión regular con los signos de puntuación personalizados
        pattern = '|'.join(re.escape(p) for p in ["?",",","."])
        # Dividimos la cadena usando la expresión regular y eliminamos los elementos vacíos
        parts = re.split(pattern, text)
        return [part for part in parts if part.strip()]