import re
import os
from nlg.reply import Reply, ReplyFormEnum, ReplyErrorEnum
from melisa_orm import ThreadEnum, ChatStatusEnum, ChatKindEnum, Question, ChatWhomEnum,Thread,Chat
from forms.croppie import Croppie
import uuid
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
                    #questions_pending = [q for q, c in zip(questions, history_chats) if (q.name != c.slots["question"] and c.status == ChatStatusEnum.OK) and (q.name != chat.slots["question"] and chat.status == ChatStatusEnum.OK)]

                    #questions_pending = [q for q, c in zip(questions, history_chats) if (q.name != c.slots["question"])]
                    #print("Preguntas pendientes 1",len(questions_pending))
                    #questions_wrong = [q for q, c in zip(questions_pending, history_chats) if (q.name == c.slots["question"] and c.status != ChatStatusEnum.OK and c.whom == ChatWhomEnum.USER)]
                    #if questions_wrong and len(questions_wrong) > 0:
                    #    questions_pending.extend(questions_wrong)
                    #print("Preguntas pendientes 2",len(questions_pending),len(questions_wrong))

                    questions_pending = []

                    # Obtener una lista de los nombres de preguntas en history_chats
                    question_names_in_history_chats = [c.slots["question"] for c in history_chats if "question" in c.slots]


                    # Filtrar las preguntas que no están en history_chats
                    questions_pending = [q for q in questions if q.name not in question_names_in_history_chats]

                    # We check if still we need to ask more questions to users
                    if questions_pending:
                        #print("Preguntas pendientes",len(questions_pending),questions_pending[0].name)
                        answers.extend([Reply(ReplyFormEnum.QUESTION,questions_pending[0].description,{"question":questions_pending[0].name})])
                    # If we don't have to ask more question, we should call the API
                    else:
                        #print("NO Preguntas pendientes")
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
                            self.close_thread(thread, chat, ChatStatusEnum.OK)
                            answers.extend([Reply(ReplyFormEnum.RECEIVED_OK)])
                            print("croppie farm ended calling api")
                            chat = Chat.objects(thread=thread.id, whom="user")
                            slots_first_post=[c.slots for c in chat]
                            slots_fixed = [entry for entry in slots_first_post if entry]
                            params = {}
                            images = {}


                            for entry in slots_fixed:
                                if entry['question'] in ['plot_area', 'altitude', 'region_id', 'variety_id','plants_count']:
                                    key = entry['question']
                                    value = entry.get('AD]', '')
                                    params[key] = value
                                elif 'media0' in entry:
                                    key = entry['question']
                                    value = entry['media0']
                                    images[key] = value

                            print(params)
                            region_id = int(params.get('region_id', ''))
                            variety_id = int(params.get('variety_id', ''))
                            plot_area = int(params.get('plot_area', ''))
                            altitude = int(params.get('altitude', ''))
                            altitude = int(params.get('altitude', ''))
                            plants_count = int(params.get('plants_count', ''))
                            branch_counts = {entry['question'].split('_')[-1]: entry['AD]'] for entry in slots_fixed if entry['question'].startswith('branch_count_three')}
                            croppie_instance = Croppie(url="https://api.croppie.org/api")
                            response = croppie_instance.post_data(region_id, variety_id, plot_area, altitude)

                            id_plat_form=response["id"]
                            response_urls = {}
                            for key, value in images.items():
                                response = croppie_instance.post_image(value)
                                print(response)
                                response_urls[key] = response[0]
                            coffee_plants = []

                            for branch_number, count in branch_counts.items():
                                plant_images = [
                                    {
                                        "original_url": response_urls.get(photo_key, ''),
                                        "manual_fruit_count": 0
                                    } for photo_key in images.keys() if photo_key.startswith(f'photo{branch_number}')
                                ] or []  

                                plant = {
                                    "plant_id": str(uuid.uuid4()),
                                    "plant_height": 2.5,
                                    "plant_age": 4.5,
                                    "branch_count": int(count),
                                    "plant_performance": "middle",
                                    "plant_images": plant_images
                                }

                                coffee_plants.append(plant)
                            response_post_stimation=croppie_instance.post_plant_data(plants_count,coffee_plants,id_plat_form)
                            id_stimation=response_post_stimation["id"]
                            estimation=croppie_instance.get_coffee_yield_estimate(id_stimation)
                            print(estimation)
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
