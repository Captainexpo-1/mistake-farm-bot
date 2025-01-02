from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Response
from src.utils import cprint, DebugColor, remove_prefix_ignore_case
import os, random
import hashlib
import time

awaiting_confirmation: dict[any, tuple[str, int]] = {}
replies_allowed: dict[int, str] = {}

timeout = {}

RATELIMIT = 60 # 1 minute

def resp_200(): return Response("OK", status=200) 

def check_ratelimits():
    keys = list(timeout.keys())
    for key in keys:
        if key not in timeout:
            continue
        if time.time() - timeout[key] > RATELIMIT:
            timeout.pop(key)

def send_message(client, user, hashed_user, text, allow_rep=False):
    p=time.process_time_ns()
    if allow_rep:
        client.chat_postMessage(
            channel=user,
            text="Allowing replies..."
        )
        replies_allowed[p] = user
        
    client.chat_postMessage(
        channel=os.environ["CHANNEL_MANAGER_ID"],
        text=f"Anonymous message: {text}"
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
        return resp_200()
    
    check_ratelimits()
    
    user = event["user"]
    text = event["text"]    
    hashed_user = hashlib.sha256(user.encode()).hexdigest()
    
    
    if user == os.environ["CHANNEL_MANAGER_ID"] and text[0] == "$":
        s = text[1:].split(":")
        if len(s) != 2:
            client.chat_postMessage(
                channel=os.environ["CHANNEL_MANAGER_ID"],
                text="Unable to parse message, reply format = $<ID>:<Message>"
            )
            return resp_200()
        id = int(s[0].strip())
        msg = s[1].strip()
    
        if (reply_channel:=replies_allowed.get(id)) != None:
            if msg.lower() in ["n", "no"]:
                replies_allowed.pop(id)
                client.chat_postMessage(
                    channel=os.environ["CHANNEL_MANAGER_ID"],
                    text="Denied!"
                )   
            else:
                client.chat_postMessage(
                    channel=reply_channel,
                    text=f"Reply: {msg}"
                )
                client.chat_postMessage(
                    channel=os.environ["CHANNEL_MANAGER_ID"],
                    text="Reply succesful!"
                )
            return resp_200()
        else:
            client.chat_postMessage(
                channel=os.environ["CHANNEL_MANAGER_ID"],
                text="Cannot find ID."
            )
            return resp_200()
    
    if hashed_user in timeout:
        client.chat_postMessage(
            channel=user,
            text=f"Please wait {RATELIMIT - (time.time() - timeout[hashed_user]):.2f} seconds before sending another message."
        )
        return resp_200()
    
    text: str = ""
    if (text := awaiting_confirmation.get(hashed_user)) != None:
        confirmed = text.lower() in ["y", "yes"]
        if not confirmed:
            client.chat_postMessage(
                channel=user,
                text="Aborting!"
            )
            awaiting_confirmation.pop(hashed_user)
            return resp_200()
        
        can_reply = text.lower().strip().startswith("(allow reply)")
        if can_reply:
            text = remove_prefix_ignore_case(text, "(allow reply)").strip()
            
        send_message(client, user, hashed_user, text, allow_rep=can_reply)  
    else:
        client.chat_postMessage(
            channel=user,
            text="Are you sure you want to send this? (y/n)"
        )
        awaiting_confirmation[hashed_user] = text    
    return resp_200()   