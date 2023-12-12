import os
import flask
from flask import request,Response
import requests
import datetime
from flask_cors import cross_origin

from melisa_orm import Melisa, User, Thread, ThreadEnum, Chat, Form, ChatWhomEnum, ChatStatusEnum, ChatKindEnum, Intent, IntentGroupEnum

from policy_management.policy_intent import PolicyIntent
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

# Register melisa
@app.route('/api/v1/melisa/', methods=['GET'])
def register_melisa():
    if config['ENABLE_REGISTER_MELISA']:
        name = request.args.get("name")
        if not Melisa.objects(name=name) :
            melisa = Melisa(name = name, url_post = request.args.get("url_post"), token = request.args.get("token"))
            melisa.save()
            return "OK"
        else:
            return "ERROR"
    else:
        return "Not enable"

def send_message(req,melisa,messages):
    request_body = {"user_id": req.user_id, "token": melisa.token, "message_tags":req.message_tags, "chat_id":req.chat_id, "text": messages}
    response = requests.post(melisa.url_post,json=request_body)

# A route to return all of the available entries in our catalog.
@app.route('/api/v1/query/', methods=['POST'])
@cross_origin()
def api_query():
    data = request.get_json()
    files = request.files
    req = RequestMelisa(data,files)
    try:
        req.validate_request()
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
                if not User.objects(user_id=req.user_id):
                    user = User(melisa = melisa, user_id = req.user_id, tags = req.user_tags)
                    user.save()
                    # Sending welcome to new user
                    if melisa.say_hi:
                        send_message(req,melisa,Generator.print([Reply(ReplyKindEnum.NEW_USER)]))
                else:
                    user = User.objects.get(user_id=req.user_id)

                # Detect the intention
                p_intent = PolicyIntent(nlu=nlu_o)
                all_forms = Form.objects()
                int_detected = None
                slots = []
                # If message is text we detect the intention
                if kind_msg == ChatKindEnum.TEXT:
                    int_detected = p_intent.detection(req.message_normalized, all_forms=all_forms)
                    slots = int_detected.slots

                # Get latest thread and check what the chatbot should do
                current_thread = None
                recent_chats = []
                last_thread = Thread.objects(user=user).order_by('-id').first()
                now = datetime.datetime.now()

                # Validate if the last thread is still opened
                if last_thread and last_thread.status == ThreadEnum.OPENED:
                    current_thread = last_thread
                    recent_chats = Chat.objects(thread = last_thread).order_by('-id')
                else:
                    # If the latest thread is not or is closed, we create a new thread for this request
                    new_intent = Intent(id =1, name="", group= 1)
                    current_thread = Thread(user = user, intent = new_intent, status = ThreadEnum.OPENED, date = now)
                    current_thread.save()

                kind_msg = ChatKindEnum(req.kind)
                chat = Chat(thread=current_thread, date = now,
                            original = req.message_raw, text = req.message_normalized,
                            status = ChatStatusEnum.PENDING, kind_msg = kind_msg,
                            whom = ChatWhomEnum.USER, ext_id = req.chat_id,
                            slots = slots, tags=req.message_tags)

                # Check if the message is media
                if kind_msg == ChatKindEnum.IMAGE:
                    path_media = os.path.join(config['FOLDER_MEDIA'],current_thread.date.strftime("%Y%m%d"),current_thread.intent.name,str(current_thread.id))
                    os.makedirs(path_media, exist_ok=True)
                    total = 0
                    for idx, media in enumerate(req.files):
                        path_file = os.path.join(path_media,media.filename)
                        media.save(path_file)
                        slots.append({"media" + str(idx):path_file})
                        total = total + 1
                    slots.append({"total":total})
                    # Set the new slots for media messages
                    chat.slots = slots

                # Using policy depending the
                if last_thread.intent.group == IntentGroupEnum.COMMAND:
                    policy = PolicyCommand()
                    answers.extend(policy.process(current_thread, chat))
                elif last_thread.intent.group == IntentGroupEnum.QA:
                    # Validate if the melisa should answer fast and saying wait
                    if melisa.say_wait:
                        send_message(req,melisa,Generator.print([Reply(ReplyKindEnum.WAIT)]))
                    policy = PolicyQA(config["ACLIMATE_API"],",".join(melisa.countries))
                    answers.extend(policy.process(current_thread, chat, recent_chats))
                elif last_thread.intent.group == IntentGroupEnum.FORM:
                    policy = PolicyForms()
                    answers.extend(policy.process(current_thread, chat, recent_chats))

                # Generate the answer to users
                answers_generated = Generator.print(answers)
                request_body = {"user_id": melisa.user_id, "token": melisa.token, "message_tags":melisa.message_tags, "chat_id":melisa.chat_id, "text": answers_generated}
                response = requests.post(melisa.url_post,json=request_body)
                return Response("Ok",200)
            else:
                return Response("Melisa Unauthorized",401)
    except ValueError as e:
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

# nohup python api.py > demeter.log 2>&1 &