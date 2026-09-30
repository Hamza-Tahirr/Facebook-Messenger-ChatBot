import json
import urllib.error
import urllib.parse
import urllib.request

import wikipedia
from chatbot import register_call
from django.chatbot.chatbot import chat
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from messengerbot import MessengerClient, messages

# Messenger rejects text messages longer than this
MAX_MESSAGE_LENGTH = 2000

messenger = MessengerClient(access_token=settings.ACCESS_TOKEN)


def index(request):
    return render(request, "home.html")


def about(query, qtype=None):
    service_url = 'https://kgsearch.googleapis.com/v1/entities:search'
    params = {
        'query': query,
        'limit': 10,
        'key': settings.API_KEY,
    }
    if qtype:
        params['types'] = qtype
    url = service_url + '?' + urllib.parse.urlencode(params)
    unknown = f"sorry, I don't know about {query}\nIf you know about {query} please tell me."
    try:
        response = json.loads(urllib.request.urlopen(url).read())
    except (urllib.error.URLError, ValueError):
        return unknown
    items = response.get('itemListElement', [])
    if not items:
        return unknown
    result = ""
    if len(items) == 1:
        data = items[0]['result']
        if "detailedDescription" in data:
            return data['detailedDescription']["articleBody"]
        if "description" in data:
            return data['name'] + " is a " + data["description"]
        return unknown
    for element in items:
        try:
            result += element['result']['name'] + "->" + element['result']["description"]+"\n"
        except KeyError:
            pass
    return result or unknown


@register_call("tellMeAbout")
def tell_me_about(session, query):
    return about(query)


@register_call("whoIs")
def who_is(session, query):
    return about(query, qtype="Person")


@register_call("whereIs")
def where_is(session, query):
    return about(query, qtype="Place")


@register_call("whatIs")
def what_is(session, query):
    try:
        return wikipedia.summary(query)
    except Exception:
        for new_query in wikipedia.search(query):
            try:
                return wikipedia.summary(new_query)
            except Exception:
                pass
    return about(query)


def initiate_chat(sender_id):
    chat.start_new_session(sender_id)
    # Fetch the user's name from their Facebook profile
    url = "https://graph.facebook.com/v2.6/" + sender_id + "?" + urllib.parse.urlencode({
        "fields": "first_name,last_name",
        "access_token": settings.ACCESS_TOKEN,
    })
    try:
        user_info = json.load(urllib.request.urlopen(url))
    except (urllib.error.URLError, ValueError):
        return
    if "first_name" in user_info:
        user_info["name"] = user_info["first_name"]
    chat.memory[sender_id].update(user_info)


def respond_to_client(sender_id, message):
    recipient = messages.Recipient(recipient_id=sender_id)
    result = chat.respond(message, session_id=sender_id)
    response = messages.MessageRequest(
        recipient, messages.Message(text=result[:MAX_MESSAGE_LENGTH]))
    messenger.send(response)


def chat_handler(request):
    data = json.loads(request.body.decode('utf-8'))
    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            message = event.get("message", {})
            # Skip echoes of the page's own messages and attachments without text
            if message.get("is_echo") or "text" not in message:
                continue
            sender_id = event["sender"]["id"]
            if sender_id not in chat.conversation:
                initiate_chat(sender_id)
            respond_to_client(sender_id, message["text"])
    return HttpResponse("It's working")


@csrf_exempt
def web_hook(request):
    if request.method != "POST":
        token = request.GET.get('hub.verify_token')
        if settings.VALIDATION_TOKEN and token == settings.VALIDATION_TOKEN:
            return HttpResponse(request.GET.get('hub.challenge', ''))
        return HttpResponseForbidden("Failed validation. Make sure the validation tokens match.")
    return chat_handler(request)
