import re
import os
from nlg.reply import Reply, ReplyFormEnum, ReplyErrorEnum,ReplyFormCroppieEnum
from nlg.generator import Generator
from nlg.reply_system import ReplySystem
from melisa_orm import ThreadEnum, ChatStatusEnum, ChatKindEnum, Question, ChatWhomEnum,Thread,Chat
from forms.croppie import Croppie
import uuid
import time
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
        error_found = False
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
                print(f"la question current es {qc.name} y el texto es {chat.text}")
                if qc.validations:
                    for v in qc.validations:
                        print(v.exp)
                        text_ok = re.match(v.exp , chat.text)
                        print(text_ok)
                        if not text_ok:
                            print('algo paso')
                            print(v.error_msg)
                            answers.extend([Reply(ReplyErrorEnum.QUESTION_NOT_FORMAT, v.error_msg, None)])
                            answers.extend([Reply(ReplyFormEnum.QUESTION, qc.description, {"question": qc.name})])  # Add the same question again
                            chat.status = ChatStatusEnum.ERROR
                            chat.save()
                            return answers 
                            break

                # If everything is ok we save the chat and continue the flow
                if text_ok:
                    chat.status = ChatStatusEnum.OK
                    chat.save()
                    # Now you can retrieve the saved values from the chat and proceed with additional processing
                    plot_area_first = None
                    lot_area_first = None
                    chat_second_validation = Chat.objects(thread=thread.id, whom="user")
                    slots_first_validation=[c.slots for c in chat_second_validation]

                    slots_to_validate = [entry for entry in slots_first_validation if entry]
                    params_validates = {}
                    for entry in slots_to_validate:
                        if entry['question'] in ['plot_area', 'lot_area']:
                            key = entry['question']
                            value = entry.get('AD]', '')
                            params_validates[key] = value
                    if 'plot_area' in params_validates:
                        plot_area_first = int(params_validates.get('plot_area', ''))
                    if 'lot_area' in params_validates:
                        lot_area_first = int(params_validates.get('lot_area', ''))
                    if qc.name == "plants_count" and (int(chat.text) < 500 * int(lot_area_first) or int(chat.text) > 12000 * int(lot_area_first)):
                        range_message = f"El número de plantas debe estar entre {500 * int(lot_area_first)} y {12000 * int(lot_area_first)}"
                        answers.extend([Reply(ReplyErrorEnum.QUESTION_NOT_FORMAT, range_message, None)])
                        answers.extend([Reply(ReplyFormEnum.QUESTION, qc.description, {"question": qc.name})])
                        return answers
                    if qc.name == "lot_area" and int(chat.text) >= int(plot_area_first):
                        answers.extend([Reply(ReplyErrorEnum.QUESTION_NOT_FORMAT, "El área del lote no puede ser mayor que el área total de la finca", None)])
                        answers.extend([Reply(ReplyFormEnum.QUESTION, qc.description, {"question": qc.name})])
                        return answers
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
                        elif thread.intent.name == "agrilac":
                            if self.agrilac.insert_data(chat.text) == "ok":
                                answers.extend([Reply(ReplyFormEnum.RECEIVED_OK)])
                                self.close_thread(thread, chat, ChatStatusEnum.OK)
                            else:
                                answers.extend([Reply(ReplyFormEnum.RECEIVED_ERROR)])
                                self.close_thread(thread, chat, ChatStatusEnum.ERROR)
                        elif thread.intent.name == "croppie farm":
                            self.close_thread(thread, chat, ChatStatusEnum.OK)
                            print("croppie farm ended calling api")
                            # Now you can use the saved information in the chat for further processing
                            chat = Chat.objects(thread=thread.id, whom="user", status=ChatStatusEnum.OK)
                            slots_first_post=[c.slots for c in chat]
                            slots_fixed = [entry for entry in slots_first_post if entry]
                            params = {}
                            images = {}
                            
                            answers.extend([Reply(ReplyFormEnum.RECEIVED_OK)])

                            for entry in slots_fixed:
                                if entry['question'] in ['plot_area', 'altitude', 'region_id', 'variety_id','plants_count','lot_area']:
                                    key = entry['question']
                                    value = entry.get('AD]', '')
                                    params[key] = value
                                elif 'media0' in entry:
                                    key = entry['question']
                                    value = entry['media0']
                                    images[key] = value
                            print(f"los parametros son {params}")
                            region_id = int(params.get('region_id', ''))
                            variety_id = int(params.get('variety_id', ''))
                            plot_area = int(params.get('plot_area', ''))
                            altitude = int(params.get('altitude', ''))
                            altitude = int(params.get('altitude', ''))
                            plants_count = int(params.get('plants_count', ''))
                            branch_counts = {entry['question'].split('_')[-1]: entry['AD]'] for entry in slots_fixed if entry['question'].startswith('branch_count_three')}
                            croppie_instance = Croppie(url="https://api.croppie.org/api")
                            response = croppie_instance.post_data(region_id, variety_id, plot_area, altitude)
                            print(f"el branch count es {branch_counts}")
                            id_plat_form=response["id"]
                            response_urls = {}
                            for key, value in images.items():
                                response = croppie_instance.post_image(value)
                                print(response)
                                response_urls[key] = response[0]
                            coffee_plants = []
                            print(f" las respuestas son {response_urls}")
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
                            
                            while True:
                                estimation = croppie_instance.get_coffee_yield_estimate(id_stimation)
                                print(estimation["status"])
                                if estimation["status"] == "finished":
                                    print("La estimación ha finalizado con éxito.")
                                    print(estimation)
                                    # Realizar acciones adicionales si es necesario
                                    break
                                elif estimation["status"] == "failed":
                                    print("La estimación ha fallado.")
                                    answers.extend([Reply(ReplyFormEnum.RECEIVED_ERROR)])
                                    # Realizar acciones adicionales si es necesario
                                    break
                                elif estimation["status"] == "running":
                                    print("La estimación aún está en progreso. Esperando...")
                                    time.sleep(5)
                                elif estimation["status"] == "queued":
                                    print("La estimación esta programada...")
                                    time.sleep(5)   # Esperar 10 segundos antes de volver a verificar
                                else:
                                    print("Estado desconocido de la estimación. Saliendo del bucle.")
                                    break
                            answers.extend([Reply(ReplyFormCroppieEnum.FINISHED_ESTIMATION,estimation)])
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
