import os
from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv

from api.chatbot import Chatbot
from api.botservice.gpt_botservice import GPTBotService
from api.servicehandler import ServiceHandler
from api.locationhandler.botservicelocationhandler import BotServiceLocationHandler
from db_funcs.file_storage import PDFStorageInterface
from db_funcs.chat_history import ChatHistoryInterface
from db_funcs.cluster_storage import ClusterStorageInterface
from utils import setup_mongo_db

load_dotenv()
# TODO: add logging of creation

api_key = os.environ["OPENAI_API_KEY"]
openai_client = OpenAI(api_key=api_key)
botservice = GPTBotService(openai_client)

mongo_db = setup_mongo_db()
chat_history = ChatHistoryInterface(mongo_db)
pdf_storage = PDFStorageInterface(mongo_db)
cluster_storage = ClusterStorageInterface(mongo_db)
location_handler = BotServiceLocationHandler(botservice)
service_handler = ServiceHandler(botservice, location_handler)

chatbot_obj = Chatbot(pdf_storage, chat_history, cluster_storage, botservice, service_handler)

app = Flask(__name__)

cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


@app.route('/')
def index():
    return "hello"


@app.route('/generate/', methods=['POST'])
@cross_origin()
def generate():
    try:
        data = request.get_json()
        # TODO: add logging

        # Validate required keys
        if not all(key in data for key in ('username', 'message', 'usertype')):
            return jsonify({'error': 'Missing required fields'}), 400

        username = data['username']
        message = data['message']
        usertype = data['usertype']

        # Validate usertype
        valid_usertypes = ['child', 'adult', 'researcher']
        if usertype.lower() not in valid_usertypes:
            return jsonify({'error': 'Invalid usertype'}), 400

        # Call the chat function
        response = chatbot_obj.chat(message, username, usertype)

        return jsonify({'response': response}), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'An error occurred while processing the request'}), 500


if __name__ == "__main__":
    # print("Populating database")
    # chatbot_obj.populate_pdfs('../pdfs')
    # chatbot_obj.add_pdf("../pdfs/autism_handbook.pdf")
    # print("Chatting")
    # print(chatbot_obj.chat("Hello", "Bob", "Adult"))
    print("Cleared")
    chatbot_obj.clear_history("Michael")
    pass
