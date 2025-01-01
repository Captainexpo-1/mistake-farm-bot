from flask import Flask, request, Response 
from dotenv import load_dotenv
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from src.events.handlers import handlers
from .utils import cprint, ColorType
load_dotenv()

app = Flask(__name__)

slack_token = os.environ["BOT_OAUTH_TOKEN"]
client = WebClient(token=slack_token)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json
    
    if data.get("event"): print(data.get("event"))
    
    if "challenge" in data:
        return Response(data["challenge"], mimetype="text/plain")
    
    if "event" in data:
        handler = handlers.get(data["event"]["type"])
        if handler:
            try:
                return handler(client, data["event"])
            except SlackApiError as e:
                assert e.response["error"]
                cprint(f"An error occurred: {e.response['error']}", ColorType.RED)
                return Response(f"An error occurred: {e.response['error']}", status=400)
        else:
            return Response("Event not supported", status=400)
    return Response("OK", status=200)

if __name__ == '__main__':
    #if os.environ.get('FLASK_ENV') == 'development':
    #    app.debug = True
        
    port = os.environ.get('PORT', 5000)
    print(f"Starting server on port {port}")
    app.run(port=port)
            