from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Response
from src.utils import cprint, DebugColor
import os, random
import hashlib
import time

awaiting_confirmation: dict[any, str] = {}

sent = {}

RATELIMIT = 120 # 2 minutes

def check_ratelimits():
    keys = list(sent.keys())
    for key in keys:
        if key not in sent:
            continue
        if time.time() - sent[key] > RATELIMIT:
            sent.pop(key)

def on_user_dm_event(client: WebClient, event: dict) -> Response:    
    if os.environ["ALLOW_ANONYMOUS_MESSAGING"] == "false":
        client.chat_postMessage(
            channel=event["user"],
            text="Anonymous messaging is disabled."
        )
        return Response("OK", status=200)
    
    user = event["user"]
    text = event["text"]    
    hashed_user = hashlib.sha256(user.encode()).hexdigest()
    
    check_ratelimits()
    
    if hashed_user in sent:
        client.chat_postMessage(
            channel=user,
            text=f"Please wait {RATELIMIT - (time.time() - sent[hashed_user]):.2f} seconds before sending another message."
        )
        return Response("OK", status=200)
    
    if (t:=awaiting_confirmation.get(hashed_user)) != None:
        confirmed_send = text.lower() in ["y", "yes"]
        if not confirmed_send:
            client.chat_postMessage(
                channel=user,
                text="Aborting!"
            )
            awaiting_confirmation.pop(hashed_user)
        else:
            client.chat_postMessage(
                channel=os.environ["CHANNEL_MANAGER_ID"],
                text=f"Anonymous message: {t}"
            )
            awaiting_confirmation.pop(hashed_user)
            client.chat_postMessage(
                channel=user,
                text="Message sent!"
            )
            sent[hashed_user] = time.time()
    else:
        client.chat_postMessage(
            channel=user,
            text="Are you sure you want to send this? (y/n)"
        )
        awaiting_confirmation[hashed_user] = text    
    return Response("OK", status=200)   