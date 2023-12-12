from policy_management.policy_intent import PolicyKnownEnum
from nlg.reply import ReplyKindEnum, Reply
from melisa_orm import ThreadEnum, ChatStatusEnum

class PolicyCommand():

    def __init__(self):
        pass

    def process(self, thread, chat):
        answers = []
        # Save the chat with the new status
        chat.status = ChatStatusEnum.OK
        chat.save()
        # Close the thread
        thread.status = ThreadEnum.CLOSED
        thread.save()
        if thread.intent.id == PolicyKnownEnum.HI:
            answers.append(Reply(ReplyKindEnum.HI))
        elif thread.intent.id == PolicyKnownEnum.BYE:
            answers.append(Reply(ReplyKindEnum.BYE))
        elif thread.intent.id == PolicyKnownEnum.HELP:
            answers.append(Reply(ReplyKindEnum.HELP))
        elif thread.intent.id == PolicyKnownEnum.THANKS:
            answers.append(Reply(ReplyKindEnum.THANKS))
        return answers
