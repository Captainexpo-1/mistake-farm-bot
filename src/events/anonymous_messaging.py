from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Response
from src.utils import cprint, DebugColor
import os, random
import hashlib
import time

awaiting_confirmation: dict[any, tuple[str, int]] = {}
replies_allowed: dict[int, str] = {}

timeout = {}

RATELIMIT = 60 # 1 minute

def check_ratelimits():
    keys = list(timeout.keys())
    for key in keys:
        if key not in timeout:
            continue
        if time.time() - timeout[key] > RATELIMIT:
            timeout.pop(key)

def send_message(client, user, hashed_user, t, allow_rep=False):
    p=time.process_time_ns()
    if allow_rep:
        client.chat_postMessage(
            channel=user,
            text="Allowing replies..."
        )
        replies_allowed[p] = user
        
    client.chat_postMessage(
        channel=os.environ["CHANNEL_MANAGER_ID"],
        text=f"Anonymous message: {t}"
    )
    if allow_rep:
        client.chat_postMessage(
            channel=os.environ["CHANNEL_MANAGER_ID"],
            text=f"Reply? ID={p} (send 'n' to deny):"
        )
    awaiting_confirmation.pop(hashed_user)
    client.chat_postMessage(
        channel=user,
        text="Message sent!"
    )
    timeout[hashed_user] = time.time()

def on_user_dm_event(client: WebClient, event: dict) -> Response:    
    if os.environ["ALLOW_ANONYMOUS_MESSAGING"] == "false":
        client.chat_postMessage(
            channel=event["user"],
            text="Anonymous messaging is disabled."
        )
        return Response("OK", status=200)
    
    check_ratelimits()
    
    user = event["user"]
    text = event["text"]    
    hashed_user = hashlib.sha256(user.encode()).hexdigest()
    
    
    if user == os.environ["CHANNEL_MANAGER_ID"] and text.startswith("REPLY:"):
        s = text.split(":")[1:]
        if len(s) != 2:
            client.chat_postMessage(
                channel=user,
                text="Unable to parse message, format = REPLY:<ID>:<Message>"
            )
            return
        id = s[0].strip()
        msg = s[1].strip()
    
        if (m:=replies_allowed.get(id)) != None:
            if msg.lower() in ["n", "no"]:
                replies_allowed.pop(id)
                client.chat_postMessage(
                    channel=user,
                    text="Denied!"
                )   
                return
            client.chat_postMessage(
                channel=m[0],
                text=msg
            )
            return
        else:
            client.chat_postMessage(
                channel=user,
                text="Cannot find ID."
            )
            return
        return
    
    if hashed_user in timeout:
        client.chat_postMessage(
            channel=user,
            text=f"Please wait {RATELIMIT - (time.time() - timeout[hashed_user]):.2f} seconds before sending another message."
        )
        return Response("OK", status=200)
    
    if (t:=awaiting_confirmation.get(hashed_user)) != None:
        confirmed = text.lower() in ["y", "yes"]
        if t[1] == 1:
            if not confirmed:
                client.chat_postMessage(
                    channel=user,
                    text="Aborting!"
                )
                awaiting_confirmation.pop(hashed_user)
                return Response("OK", status=200)
            else:
                client.chat_postMessage(
                    channel=user,
                    text="Do you want to allow replies? (y/n)"
                )
        elif t[1] == 2:
            send_message(client, user, hashed_user, t, allow_rep=confirmed)
                
        
    else:
        client.chat_postMessage(
            channel=user,
            text="Are you sure you want to send this? (y/n)"
        )
        awaiting_confirmation[hashed_user] = (text, 1)    
    return Response("OK", status=200)   