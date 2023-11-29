import flask
from flask import request,Response
import requests
from mongoengine import *
from orm.orm_demeter import *
import datetime
from flask_cors import cross_origin

from nlu.enums import Intent, Commands
from nlu.nlu_tasks import NLUTasks
from policy_management.policy_management import PolicyManagement
from policy_management.ner import NER
from policy_management.request_melisa import RequestMelisa
from nlg.generator import Generator

from data_store.agrilac import AgriLac

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
#@app.route('/api/v1/query/', methods=['GET'])
@app.route('/api/v1/query/', methods=['POST'])
@cross_origin()
def api_query():
    data = request.get_json()
    req = RequestMelisa(data)
    try:
        #say_wait = True
        #say_hi = True
        # Validate if melisa exists into the database
        if not Melisa.objects(name=req.melisa_name):
            return Response("Melisa unknown",400)
        else:
            melisa = Melisa.objects.get(name=req.melisa_name)
            # Validate authentication
            if(melisa.token == req.melisa_token):

                user = None
                # Check if the user is new
                if not User.objects(user_id=req.user_id):
                    user = User(melisa = melisa, user_id = req.user_id, tags = req.user_tags)
                    user.save()
                    # Sending welcome to new user
                    if melisa.say_hi:
                        new_user_msg = Generator.print([NER(Commands.NEW_USER)])
                        send_message(req,melisa,new_user_msg)
                else:
                    user = User.objects.get(user_id=req.user_id)

                recent_chats = Chat.objects(user = user).order_by('-date').limit(10)
                # message
                policy = PolicyManagement(config["ACLIMATE_API"],",".join(melisa.countries))
                

                # Create chat
                chat = Chat(user = user, text = message, date = datetime.datetime.now(), ext_id = chat_id, tags=message_tags)
                chat.save()

                answer = []
                # Check some especial words
                if message.lower().startswith(("hola", "hi")) and say_hi:
                    answer.append(NER(Commands.HI))
                    chat.intent_id = 6
                    chat.intent_name = "hi"
                    chat.slots = {}
                    chat.save()
                elif message.lower().startswith(("bye", "adios", "chao")):
                    answer.append(NER(Commands.BYE))
                    chat.intent_id = 7
                    chat.intent_name = "bye"
                    chat.slots = {}
                    chat.save()
                elif message.lower().startswith(("help","ayuda","command", "comando")):
                    answer.append(NER(Commands.HELP))
                    chat.intent_id = 8
                    chat.intent_name = "help"
                    chat.slots = {}
                    chat.save()
                elif message.lower().startswith(("thank","gracias")):
                    answer.append(NER(Commands.THANKS))
                    chat.intent_id = 9
                    chat.intent_name = "thanks"
                    chat.slots = {}
                    chat.save()
                # It is for agrilac project
                elif message.lower().startswith("dato preliminar"):
                    if agrilac.dato_preliminar(message) == "ok":
                        answer.append(NER(Commands.RECEIVED_OK))
                    else:
                        answer.append(NER(Commands.RECEIVED_ERROR))
                    chat.intent_id = 10
                    chat.intent_name = "agrilac"
                    chat.slots = {}
                    chat.save()
                else:
                    # Temporal message
                    if say_wait:
                        rb_tmp = {"user_id": user_id, "token": melisa.token, "message_tags":message_tags, "chat_id":chat_id, "text": ["Estoy buscando la información solicitada"]}
                        response = requests.post(melisa.url_post,json=rb_tmp)
                    # Se revisa que diga hola este en true, sino quiere decir que este es un saludo inicial
                    if say_hi:
                        # Decoded message
                        utterance = nlu_o.nlu(message)
                        print(utterance)
                        # Update chat
                        chat.intent_id = utterance["intent"]
                        chat.intent_name = utterance["name"]
                        chat.slots = utterance["slots"]
                        chat.save()

                        intent = Intent(utterance["intent"])
                        entities = utterance["slots"]

                        if(intent == Intent.PLACES):
                            answer = policy.geographic(entities)
                        elif(intent == Intent.CULTIVARS):
                            answer = policy.cultivars(entities)
                        elif(intent == Intent.CLIMATOLOGY):
                            answer = policy.historical_climatology(entities)
                        elif(intent == Intent.FORECAST_PRECIPITATION):
                            answer = policy.forecast_climate(entities)
                        elif(intent == Intent.FORECAST_YIELD):
                            answer = policy.forecast_yield(entities)
                        elif(intent == Intent.FORECAST_DATE):
                            answer = policy.forecast_yield(entities, best_date=True)

                answers = Generator.print(answer)
                request_body = {"user_id": user_id, "token": melisa.token, "message_tags":message_tags, "chat_id":chat_id, "text": answers}
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