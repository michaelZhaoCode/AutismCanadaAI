import os
from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv

from api.chatbot import Chatbot
from api.botservice.gpt_botservice import GPTBotService
from api.servicehandler.botservice_servicehandler import BotserviceServiceHandler
from api.locationdatabase.sqlitelocationdatabase import SQLiteLocationDatabase
from db_funcs.file_storage import PDFStorageInterface
from db_funcs.chat_history import ChatHistoryInterface
from db_funcs.cluster_storage import ClusterStorageInterface
from utils import setup_mongo_db

load_dotenv()
# TODO: add logging of creation

api_key = os.environ["OPENAI_API_KEY"]
openai_client = OpenAI(api_key=api_key)
botservice = GPTBotService(openai_client)

location_database = SQLiteLocationDatabase()
location_database.initialize_database()
location_database.create_snapshot()

mongo_db = setup_mongo_db()
chat_history = ChatHistoryInterface(mongo_db)
pdf_storage = PDFStorageInterface(mongo_db)
cluster_storage = ClusterStorageInterface(mongo_db)
service_handler = BotserviceServiceHandler(botservice, location_database)

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

        username = data.get('username')
        message = data.get('message')
        usertype = data.get('usertype')
        location = data.get('location', "")
        region_id = data.get('region_id', -1)

        # Validate usertype
        valid_usertypes = ['child', 'adult', 'researcher']
        if usertype.lower() not in valid_usertypes:
            return jsonify({'error': 'Invalid usertype'}), 400

        # Validate and cast region_id to int
        if region_id:
            try:
                region_id = int(region_id)  # Attempt to cast to int
            except ValueError:
                return jsonify({'error': 'region_id must be an integer'}), 400

        # Call the chat function
        response = chatbot_obj.chat(message, username, usertype, location, region_id)

        return jsonify({'response': response}), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'An error occurred while processing the request'}), 500


@app.route('/retrieve_regions', methods=['GET'])
@cross_origin()
def retrieve_regions():
    try:
        results = location_database.load_snapshot()
        return jsonify({'response': results}), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'An error occurred while retrieving regions'}), 500


if __name__ == "__main__":
    # print("Populating database")
    # chatbot_obj.populate_pdfs('../pdfs')
    # chatbot_obj.add_pdf("../pdfs/autism_handbook.pdf")
    # print("Chatting")
    # print(chatbot_obj.chat("Hello", "Bob", "Adult"))
    # print("Cleared")
    # chatbot_obj.clear_history("Michael")
    pass
