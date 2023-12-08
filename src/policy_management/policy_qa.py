from policy_intent import PolicyKnownEnum
from nlg.reply import ReplyKindEnum, Reply, ReplyErrorEnum
from melisa_orm import ThreadEnum, ChatStatusEnum,ChatWhomEnum
from aclimate.aclimate import AClimate

class PolicyQA():

    def __init__(self, url, countries):
        self.aclimate_client = AClimate(url,countries)

    # Close the thread
    def close_thread(self, thread, chat, status):
        # Save the chat with the new status
        chat.status = status
        chat.save()

        thread.status = ThreadEnum.CLOSED
        thread.save()

    def process(self, thread, chat, history_chats):
        answers = []

        if thread.intent.id == PolicyKnownEnum.PLACES:
            # Check if the current message has the data needed
            if "locality" in chat.slots:
                answers.extend(self.aclimate_client.geographic(chat.slots["locality"]))
                self.close_thread(thread, chat, ChatStatusEnum.OK)
            # If the message don't have the data needed we analyze all chats of the thread
            elif history_chats:
                chat.slots = [{"locality":chat.text}]
                answers.extend(self.aclimate_client.geographic(chat.text))
                self.close_thread(thread, chat, ChatStatusEnum.OK)
            else:
                answers.extend(Reply(ReplyErrorEnum.MISSING_LOCALITIES))
                chat.save()

        elif thread.intent.id == PolicyKnownEnum.CULTIVARS:
            crop = chat.slots["crop"] if "crop" in chat.slots else None
            cultivar = chat.slots["cultivar"] if "cultivar" in chat.slots else None
            answers.extend(self.aclimate_client.cultivars(crop,cultivar))
            self.close_thread(thread)

        elif thread.intent.id == PolicyKnownEnum.CLIMATOLOGY:
            # Check if the current message has the data needed
            if "locality" in chat.slots:
                answers.extend(self.aclimate_client.historical_climatology(chat.slots["locality"]))
                self.close_thread(thread, chat, ChatStatusEnum.OK)
            # If the message don't have the data needed we analyze all chats of the thread
            elif history_chats:
                chat.slots = [{"locality":chat.text}]
                answers.extend(self.aclimate_client.geographic(chat.text))
                self.close_thread(thread, chat, ChatStatusEnum.OK)
            else:
                answers.extend(Reply(ReplyErrorEnum.MISSING_LOCALITIES))
                chat.save()

        elif thread.intent.id == PolicyKnownEnum.FORECAST_PRECIPITATION:
            # Check if the current message has the data needed
            if "locality" in chat.slots:
                answers.extend(self.aclimate_client.forecast_climate(chat.slots["locality"]))
                self.close_thread(thread, chat, ChatStatusEnum.OK)
            # If the message don't have the data needed we analyze all chats of the thread
            elif history_chats:
                chat.slots = [{"locality":chat.text}]
                answers.extend(self.aclimate_client.geographic(chat.text))
                self.close_thread(thread, chat, ChatStatusEnum.OK)
            else:
                answers.extend(Reply(ReplyErrorEnum.MISSING_LOCALITIES))
                chat.save()

        elif thread.intent.id == PolicyKnownEnum.FORECAST_YIELD or thread.intent.id == PolicyKnownEnum.FORECAST_DATE:
            best_date = False if thread.intent.id == PolicyKnownEnum.FORECAST_YIELD else True
            cultivar = chat.slots["cultivar"] if "cultivar" in chat.slots else None
            crop = chat.slots["crop"] if "crop" in chat.slots else None
            # Check if the current message has the data needed
            if "locality" in chat.slots:
                answers.extend(self.aclimate_client.forecast_yield(chat.slots["locality"], best_date = best_date, cultivar=cultivar, crop=crop))
                self.close_thread(thread, chat, ChatStatusEnum.OK)
            # If the message don't have the data needed we analyze all chats of the thread
            elif history_chats:
                chat.slots = [{"locality":chat.text}]
                answers.extend(self.aclimate_client.geographic(chat.text))
                self.close_thread(thread, chat, ChatStatusEnum.OK)
            else:
                answers.extend(Reply(ReplyErrorEnum.MISSING_LOCALITIES))
                chat.save()
        return answers
