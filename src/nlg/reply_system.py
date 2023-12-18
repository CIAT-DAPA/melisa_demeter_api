# Class representing a generic reply from the system
class ReplySystem():

    # Constructor for the ReplySystem class
    def __init__(self, type, messages, slots = None):
        """
        Initializes a new instance of the ReplySystem class.

        Parameters:
        - type: Type of the reply (uses enums defined above).
        - messages: Array of messages to send to the users
        - slots: Optional text
        """
        self.type = type
        self.messages = messages
        self.slots = slots