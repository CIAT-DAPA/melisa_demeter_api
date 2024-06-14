import os
import flask
import traceback
from flask import request,Response
import requests
import datetime
from flask_cors import cross_origin
from mongoengine import *
import json
from melisa_orm import Melisa, User, Thread, ThreadEnum, Chat, Form, ChatWhomEnum, ChatStatusEnum, ChatKindEnum, Intent, IntentGroupEnum
from forms.cenaos import GoogleSheetManager
from policy_management.policy_intent import PolicyIntent,PolicyKnownEnum
from policy_management.policy_command import PolicyCommand
from policy_management.policy_forms import PolicyForms
from policy_management.policy_qa import PolicyQA

from nlu.nlu_tasks import NLUTasks
from nlu.request_melisa import RequestMelisa

from nlg.reply import Reply, ReplyKindEnum
from nlg.generator import Generator

from forms.agrilac import AgriLac

from conf import config

app = flask.Flask(__name__)

nlu_o = None
agrilac = None

# Home page
@app.route('/', methods=['GET'])
def home():
    return "<h1>Demeter Bot</h1>"

def send_message(req,melisa,messages):
    request_body = {"user_id": req.user_id, "token": melisa.token, "message_tags":req.message_tags, "chat_id":req.chat_id, "text": messages}
    print(f"request body{request_body}")
    response = requests.post(melisa.url_post,json=request_body)

# A route to return all of the available entries in our catalog.
@app.route('/api/v1/query/', methods=['POST'])
@cross_origin()
def api_query():
    #data = request.get_json()
    print(request.form)
    data = request.form.to_dict()
    if data.get("user_tags.service") =="facebook" or data.get("user_tags.service") == "whatsapp":
        print("es whatsapp o facebook")
        user_tags = {}
        message_tags = {}

        for key, value in data.items():
            if key.startswith('user_tags.'):
                user_tags[key.split('.')[1]] = value
            elif key.startswith('message_tags.'):
                message_tags[key.split('.')[1]] = value

# Agregar los diccionarios al diccionario original
        data['user_tags'] = user_tags
        data['message_tags'] = message_tags

    print(f"la data es {data}")
    #print("Request Content:", content)
    #print("original json",request.json)
    #print("json",data)
    #print("data",)
    #print("melisa",data["melisa"])
    files = request.files if request.files else None
    req = RequestMelisa(data,files)
    try:
        req.validate_request()
        #print("validate", req)
        # Validate if melisa exists into the database
        
        if not Melisa.objects(name=req.melisa_name):
            return Response("Melisa unknown",400)
        else:
            melisa = Melisa.objects.get(name=req.melisa_name)
            # Validate authentication
            if(melisa.token == req.melisa_token):
                answers = []
                user = None
                # Check if the user is new
                if(type(req.user_tags) == str):
                        print("user_tags is srt")
                        req.user_tags = {}
                if not User.objects(user_id=req.user_id):   
                    print("user_tags",req.user_tags)
                    user = User(melisa = melisa, user_id = req.user_id, tags = req.user_tags)
                    user.save()
                    # Sending welcome to new user
                    if melisa.say_hi:
                        an_sys = Generator.print([Reply(ReplyKindEnum.NEW_USER)])
                        send_message(req,melisa,an_sys[0].messages)
                else:
                    user = User.objects.get(user_id=req.user_id)

                ##########################################
                # NLU
                ##########################################
                # Detect the intention
                p_intent = PolicyIntent(nlu=nlu_o)
                all_forms = Form.objects()
                int_detected = None
                slots = {}
                # If message is text we detect the intention
                #print("kind",req.kind, req.kind_msg == ChatKindEnum.TEXT)
                if req.kind_msg == ChatKindEnum.TEXT:
                    int_detected = p_intent.detection(req.message_normalized, all_forms=all_forms)
                    slots = int_detected.slots

                ##########################################
                # STATUS TRACE
                ##########################################

                # Get latest thread and check what the chatbot should do
                current_thread = None
                recent_chats = []
                last_thread = Thread.objects(user=user).order_by('-id').first()
                now = datetime.datetime.now()

                # Validate if the last thread is still opened
                if last_thread and last_thread.status == ThreadEnum.OPENED:
                    current_thread = last_thread
                    recent_chats = Chat.objects(thread = last_thread).order_by('-id')
                # If the latest thread is not or is closed, we create a new thread for this request
                else:
                    new_intent = None
                    if req.kind_msg == ChatKindEnum.TEXT:
                        new_intent = Intent(id = int_detected.id, name=int_detected.detected, group= int_detected.group)
                    else:
                        new_intent = Intent(id = -1, name="", group= IntentGroupEnum.UNKONW)
                    current_thread = Thread(user = user, intent = new_intent, status = ThreadEnum.OPENED, date = now)
                    current_thread.save()

                kind_msg = ChatKindEnum(req.kind)
                chat = Chat(thread=current_thread, date = now,
                            original = req.message_raw, text = req.message_normalized,
                            status = ChatStatusEnum.PENDING, kind_msg = kind_msg,
                            whom = ChatWhomEnum.USER, ext_id = req.chat_id,
                            slots = slots, tags=req.message_tags)

                # Check if the message is media
                if req.kind_msg == ChatKindEnum.IMAGE:
                    path_media = os.path.join(config['FOLDER_MEDIA'],current_thread.date.strftime("%Y%m%d"),current_thread.intent.name,str(current_thread.id))
                    os.makedirs(path_media, exist_ok=True)
                    total = 0
                    for idx, media_name in enumerate(req.files):
                        media = request.files[media_name]
                        path_file = os.path.join(path_media,media.filename)
                        media.save(path_file)
                        slots["media" + str(idx)] = path_file
                        total = total + 1
                    slots["total_files"] = total
                    # Set the new slots for media messages
                    chat.slots = slots

                ##########################################
                # POLICY
                ##########################################

                # Using policy depending the
                if IntentGroupEnum(current_thread.intent.group) == IntentGroupEnum.COMMAND:
                    policy = PolicyCommand()
                    answers.extend(policy.process(current_thread, chat))
                elif IntentGroupEnum(current_thread.intent.group) == IntentGroupEnum.QA:
                    # Validate if the melisa should answer fast and saying wait
                    if melisa.say_wait:
                        an_sys = Generator.print([Reply(ReplyKindEnum.WAIT)])
                        print(an_sys)
                        send_message(req,melisa,an_sys[0].messages)
                    policy = PolicyQA(config["ACLIMATE_API"],",".join(melisa.countries))
                    answers.extend(policy.process(current_thread, chat, recent_chats))
                elif IntentGroupEnum(current_thread.intent.group) == IntentGroupEnum.FORM:
                    forms = [f for f in all_forms if f.command == current_thread.intent.name]
                    policy = PolicyForms(config['FOLDER_MEDIA'],agrilac=agrilac)
                    answers.extend(policy.process(current_thread, chat, recent_chats,forms[0]))

                ##########################################
                # NLG
                ##########################################

                # Generate the answer to users
                answers_generated = Generator.print(answers)
                text_generated = []
                now2 = datetime.datetime.now()
                for ag in answers_generated:
                    for m in ag.messages:
                        print(f"el mensaje es {m}")
                        chat_sys = Chat(thread=current_thread, date = now2,
                                original = str(ag.type), text = m,
                                status = ChatStatusEnum.OK, kind_msg = ChatKindEnum.TEXT,
                                whom = ChatWhomEnum.SYSTEM, ext_id = req.chat_id,
                                slots = ag.slots, tags=req.message_tags)
                        chat_sys.save()
                        text_generated.append(m)
                send_message(req,melisa,text_generated)
                return Response("Ok",200)
            else:
                return Response("Melisa Unauthorized",401)
    #except Exception as e:
    except ValueError as e:
        print("error",e)
        traceback.print_exc()
        return Response("Request incomplete",401)


if __name__ == "__main__":
    # It starts the model for NLU
    nlu_o  = NLUTasks(model_path = config['MODEL_PATH'], params_path = config['PARAMS_PATH'])
    print("NLU loaded")

    # Connect with database
    connect(host=config['CONNECTION_DB'])
    print("Connected DB")

    # Data for google drive agrilac
    agrilac = AgriLac(config['AGRILAC_KEY'],config['AGRILAC_FILE'],config['AGRILAC_SHEET'])
    print("Connected to google sheet agrilac")

    if config['DEBUG']:
        app.run(threaded=True, port=config['PORT'], debug=config['DEBUG'])
    else:
        app.run(host=config['HOST'], port=config['PORT'], debug=config['DEBUG'])
        #app.run(host=config['HOST'], port=config['PORT'], debug=True)

# nohup python api.py > demeter.log 2>&1 &