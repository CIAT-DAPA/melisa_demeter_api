import re
import os
from nlg.reply import Reply, ReplyFormEnum, ReplyErrorEnum
from melisa_orm import ThreadEnum, ChatStatusEnum, ChatKindEnum, Question, ChatWhomEnum, ChatKindEnum

class PolicyForms():

    def __init__(self, folder_media, agrilac = None, croppie = None):
        self.folder_media = folder_media
        self.agrilac = agrilac
        self.croppie = croppie

    # Close the thread
    def close_thread(self, thread, chat, status):
        # Save the chat with the new status
        chat.status = status
        chat.save()

        thread.status = ThreadEnum.CLOSED
        thread.save()

    def process(self, thread, chat, history_chats, form):
        answers = []
        questions = Question.objects(form=form).order_by('order')

        # Check if it has history in the chats. if it doesn't have it is the first question
        if history_chats:
            # We should take the latest question
            if history_chats.first().whom == ChatWhomEnum.SYSTEM:
                for key, value in history_chats.first().slots.items():
                    chat.slots[key] = value

                # Validation
                question_current = [q for q in questions if q.name == chat.slots["question"]]
                qc = question_current[0]
                text_ok = True
                # Loop to check all validations of the questions
                if qc.validations:
                    for v in qc.validations:
                        text_ok = re.match(v.exp , chat.text)
                        # If the question doesn't accomplish with the requirements
                        # change the status of the chat and stop
                        if not text_ok:
                            answers.extend([Reply(ReplyErrorEnum.QUESTION_NOT_FORMAT,v.error_msg,None)])
                            chat.status = ChatStatusEnum.ERROR
                            chat.save()
                            break

                # If everything is ok we save the chat and continue the flow
                if text_ok:
                    chat.status = ChatStatusEnum.OK
                    chat.save()

                    # remove all questions did until now and are OK
                    questions_pending = [q for q, c in zip(questions, history_chats) if (q.name != c.slots["question"] and c.status == ChatStatusEnum.OK) and (q.name != chat.slots["question"] and chat.status == ChatStatusEnum.OK)]
                    # We check if still we need to ask more questions to users
                    if questions_pending:
                        answers.extend([Reply(ReplyFormEnum.QUESTION,questions_pending[0].description,{"question":questions_pending[0].name})])
                    # If we don't have to ask more question, we should call the API
                    else:
                        # It is just for test
                        if thread.intent.name == "test":
                            self.close_thread(thread, chat, ChatStatusEnum.OK)
                            answers.extend([Reply(ReplyFormEnum.RECEIVED_OK)])
                        elif thread.intent.name == "agrilac":
                            if self.agrilac.insert_data(chat.text) == "ok":
                                answers.extend([Reply(ReplyFormEnum.RECEIVED_OK)])
                                self.close_thread(thread, chat, ChatStatusEnum.OK)
                            else:
                                answers.extend([Reply(ReplyFormEnum.RECEIVED_ERROR)])
                                self.close_thread(thread, chat, ChatStatusEnum.ERROR)
                        elif thread.intent.name == "croppie farm":
                            ###################
                            # CODE CROPPIE
                            self.close_thread(thread, chat, ChatStatusEnum.OK)
                        elif thread.intent.name == "croppie coffe":
                            ###################
                            # CODE CROPPIE
                            self.close_thread(thread, chat, ChatStatusEnum.OK)
            else:
                print("Second message in line")
        # It is the first question
        else:
            answers.extend([Reply(ReplyFormEnum.QUESTION, questions.first().description, {"question":questions.first().name})])
            chat.status = ChatStatusEnum.OK
            chat.save()

        return answers
