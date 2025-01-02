from flask import Flask, request, Response, jsonify
from dotenv import load_dotenv
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from src.events.handlers import handlers
from src.utils import cprint, DebugColor
import json

load_dotenv()

app = Flask(__name__)

in_dev = os.environ.get("FLASK_ENV") == "development"

slack_token = os.environ["BOT_OAUTH_TOKEN"]
client = WebClient(token=slack_token)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json
    
    if data.get("event") and in_dev: 
        print(data.get("event"))
    
    if "challenge" in data:
        return Response(data["challenge"], mimetype="text/plain")
    
    if "event" in data:
        handler = handlers.get(data["event"]["type"])
        if handler:
            try:
                return handler(client, data["event"])
            except SlackApiError as e:
                assert e.response["error"]
                cprint(f"An error occurred: {e.response['error']}", DebugColor.RED)
                return Response(f"An error occurred: {e.response['error']}", status=400)
        else:
            cprint(f"Event not supported: {data['event']['type']}", DebugColor.YELLOW)
            return Response("Event not supported", status=400)
    return Response("OK", status=200)

@app.route("/slack/interact", methods=["POST"])
def handle_interaction():
    payload = request.form.get("payload")
    data = json.loads(payload)

    if data["type"] == "block_actions":
        action_id = data["actions"][0]["action_id"]
        user_id = data["user"]["id"]

        if action_id == "submit_button":
            # Extract the text input value
            input_value = next(
                block["element"]["initial_value"]
                for block in data["message"]["blocks"]
                if block["block_id"] == "text_input_block"
            )
            print(f"User {user_id} submitted: {input_value}")

            # Send a response back to the user
            client.chat_postMessage(
                channel=user_id,
                text=f"Thanks for submitting: {input_value}"
            )

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    #if os.environ.get('FLASK_ENV') == 'development':
    #    app.debug = True
        
    port = os.environ.get('PORT', 5000)
    print(f"Starting server on port {port}")
    app.run(port=port)
            