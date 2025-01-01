from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Response
from ..utils import cprint, ColorType
import os, random


get_random_verb = lambda: random.choice([
    "skedaddle", 
    "run", 
    "hurry"
])

get_random_farm_reaction = lambda: random.choice([
    "tractor", 
    "cow", 
    "chicken",
    "farmer",
    "pig",
    "sheep",
    "eggplant",
    "corn",
])

get_random_adjective = lambda: random.choice([
    "incredible", 
    "silly", 
    "fantastic", 
    "interesting",
])

def on_message_event(client: WebClient, event: dict) -> Response:
    
    if event.get("channel") != os.environ["ACTIVE_CHANNEL_ID"]:
        return Response("OK", status=200)
    
    if "subtype" in event: return Response("OK", status=200)
    if "bot_profile" in event: return Response("OK", status=200)
    
    if "farm" in event.get("text"): 
        ts = event["ts"]
        client.reactions_add(
            channel=event["channel"],
            name=get_random_farm_reaction(),
            timestamp=ts
        )
        
    return Response("OK", status=200)
        
        
def on_member_joined_channel_event(client: WebClient, event: dict) -> Response:
    response = client.chat_postMessage(
        channel=event["channel"],
        text=f"This is incredible! It looks like <@{event['user']}> joined!"
    )
    ts = response["ts"]
    response = client.chat_postMessage(
        channel=event["channel"],
        thread_ts=ts,
        text=f"I need to {get_random_verb()} to tell <@{os.environ["CHANNEL_MANAGER_ID"]}> about this!"
    )
    response = client.chat_postMessage(
        channel=event["channel"],
        thread_ts=ts,
        text=f"In the meantime, why did you decide to join this {get_random_adjective()} channel?"
    )
    convo = client.conversations_open(users=[os.environ["CHANNEL_MANAGER_ID"]])
    response = client.chat_postMessage(
        channel=convo["channel"]["id"],
        text=f"Hey there! <@{os.environ['CHANNEL_MANAGER_ID']}>, <@{event['user']}> just joined!"
    )
    
    return Response("OK", status=200)

handlers = {
    "message": on_message_event,
    "member_joined_channel": on_member_joined_channel_event
}