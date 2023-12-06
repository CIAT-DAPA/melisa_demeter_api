
class IntentDetected():

    # Method construct
    def __init__(self, group, id, detected, slots = None):
        self.id = id
        self.group = group
        self.detected = detected
        self.slots = slots