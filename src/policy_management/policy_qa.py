from policy_intent import PolicyKnownEnum
from nlg.reply import ReplyKindEnum, Reply, ReplyErrorEnum
from melisa_orm import ThreadEnum, ChatStatusEnum,ChatWhomEnum
from aclimate.aclimate import AClimate

class PolicyQA():

    def __init__(self, url, countries):
        self.aclimate_client = AClimate(url,countries)

    def process(self, thread, chat, history_chats):
        answers = []
        # Save the chat with the new status
        chat.status = ChatStatusEnum.OK
        chat.save()

        # Close the thread
        #thread.status = ThreadEnum.CLOSED
        #thread.save()

        if thread.intent.id == PolicyKnownEnum.PLACES:
            # Check if the current message has the data needed
            if "locality" in chat.slots:
                answers.extend(self.aclimate_client.geographic(chat.slots["locality"]))
            # If the message don't have the data needed we analyze all chats of the thread
            elif history_chats:
                # If the thread is opend and the latest message was from the system the current message is the answer
                if thread.status == ThreadEnum.OPENED and history_chats[0].whom == ChatWhomEnum.SYSTEM:
                    chat.slots = [{"locality":chat.text}]
                    chat.save()
                    answers.extend(self.aclimate_client.geographic(chat.text))
                # We assume the last message was the locality because the
                else:
                    answers.extend(Reply(ReplyErrorEnum.MISSING_LOCALITIES))
            else:
                answers.extend(Reply(ReplyErrorEnum.MISSING_LOCALITIES))

        elif thread.intent.id == PolicyKnownEnum.CULTIVARS:
            answer = policy.cultivars(entities)
        elif thread.intent.id == PolicyKnownEnum.CLIMATOLOGY:
            answer = policy.historical_climatology(entities)
        elif thread.intent.id == PolicyKnownEnum.FORECAST_PRECIPITATION:
            answer = policy.forecast_climate(entities)
        elif thread.intent.id == PolicyKnownEnum.FORECAST_YIELD:
            answer = policy.forecast_yield(entities)
        elif thread.intent.id == PolicyKnownEnum.FORECAST_DATE:
            answer = policy.forecast_yield(entities, best_date=True)
        return answers
