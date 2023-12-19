from enum import Enum
from policy_management.intent_detected import IntentDetected
from melisa_orm import IntentGroupEnum

class PolicyKnownEnum(Enum):
    FORECAST_YIELD = 0
    FORECAST_PRECIPITATION = 1
    CLIMATOLOGY = 2
    CULTIVARS = 3
    PLACES = 4
    FORECAST_DATE = 5
    HI = 6
    BYE = 7
    HELP = 8
    THANKS = 9

    @staticmethod
    def list():
        return dict((label.name, idx) for idx, label in enumerate(PolicyKnownEnum))

class PolicyIntent():

    # Method construct
    def __init__(self, nlu):
        self.nlu = nlu

    # Method that try to identify the intention of the message
    # (str) msg: Message of the user
    # (list(Form)) all_forms: List of all forms registered in the database
    def detection(self, msg, all_forms):
        detected = ""
        id = 0
        group = IntentGroupEnum.COMMAND
        slots = {}
        if msg.lower().startswith(("hola", "hi")):
            detected = "hi"
            id = PolicyKnownEnum.HI.value
        elif msg.lower().startswith(("help","ayuda")):
            detected = "help"
            id = PolicyKnownEnum.HELP.value
        elif msg.lower().startswith(("bye", "adios", "chao")):
            detected = "bye"
            id = PolicyKnownEnum.BYE.value
        elif msg.lower().startswith(("thank","gracias")):
            detected = "thanks"
            id = PolicyKnownEnum.THANKS.value
        else:
            form_found = [form for form in all_forms if form.command == msg]
            if form_found:
                group = IntentGroupEnum.FORM
                detected = form_found[0].command
                id = form_found[0].ext_id
            else:
                group = IntentGroupEnum.QA
                utterance = self.nlu.nlu(msg)
                detected = utterance["name"].lower()
                id = PolicyKnownEnum[utterance["name"].upper()].value
                slots = utterance["slots"]
        intent = IntentDetected(group=group, id = id, detected=detected, slots=slots)
        #print("intent",intent.group,intent.detected,intent.slots)
        return intent