# Facebook Messenger ChatBot

A Django app that connects a Facebook Page to a template-based chatbot. Messages sent to the page arrive at a webhook, the [chatbotAI](https://github.com/ahmadfaizalbh/Chatbot) engine picks a reply from a conversation template, and the reply goes back to the user through the Messenger Send API.

It is based on [FacebookMessengerBot](https://github.com/ahmadfaizalbh/FacebookMessengerBot) by Ahmad Faizal B H. See [Credits](#credits) for what changed.

## Features

- Messenger webhook that answers Facebook's verification request and handles incoming text messages
- Replies defined in a chatbotAI template (`chatbotTemplate/Example.template`): pattern matching, several random replies per pattern and ELIZA-style small talk
- Per-user memory: "Call me ...", "What is my name?", and "Remember X is Y", which teaches the bot new questions about X
- Saves the user's first name from their Facebook profile when a conversation starts, so the template can use it in replies
- "What is ..." is answered with a Wikipedia summary; "Who is ...", "Where is ..." and "Tell me about ..." use the Google Knowledge Graph Search API
- Conversations and memory are stored in SQLite through django-chatbot

## Tech stack

- Python, Django 3.1
- chatbotAI and django-chatbot (conversation engine and database-backed sessions)
- messengerbot (Messenger Send API client)
- wikipedia package and the Google Knowledge Graph Search API
- SQLite

## Project structure

```
manage.py
fbbot/                    Django project: settings, URLs, WSGI
bot/views.py              webhook, Messenger replies and lookup functions
bot/templates/            simple home page
bot/chatbot_migrations/   database tables for django-chatbot
chatbotTemplate/          conversation template used by the bot
requirements.txt
.env.example
```

## Setup

You need Python 3.8 or 3.9 (Django 3.1 does not support newer versions), a Facebook Page with a Meta developer app that has Messenger enabled, and optionally a Google API key with the Knowledge Graph Search API turned on.

```bash
git clone https://github.com/Hamza-Tahirr/Facebook-Messenger-ChatBot.git
cd Facebook-Messenger-ChatBot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django secret key (any long random string) |
| `DJANGO_DEBUG` | `True` for local development |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names, e.g. `localhost,127.0.0.1,<your-ngrok-host>` |
| `FB_PAGE_ACCESS_TOKEN` | Page access token from the Meta app |
| `FB_VERIFY_TOKEN` | Any string; enter the same value when setting up the webhook |
| `GOOGLE_KG_API_KEY` | Google API key for the Knowledge Graph lookups |

Create the database tables, then start the server:

```bash
python manage.py migrate
python manage.py runserver
```

Run `migrate` before the first start. django-chatbot does not ship its own migrations, so the project keeps them in `bot/chatbot_migrations/` and `migrate` creates the conversation and memory tables too.

## Connecting to Messenger

1. Expose the local server over HTTPS, for example with `ngrok http 8000`, and add the ngrok host to `DJANGO_ALLOWED_HOSTS`.
2. In the Messenger settings of your Meta app, set the callback URL to `https://<your-host>/webhook` and the verify token to the value of `FB_VERIFY_TOKEN`.
3. Subscribe the page to the `messages` webhook field.
4. Send a message to the page. The bot replies to every text message; attachments and stickers are ignored.

## Changing the conversation

Edit `chatbotTemplate/Example.template` to change what the bot says. Functions in `bot/views.py` decorated with `@register_call("name")` can be called from the template with `{% call name:%1 %}`, which is how the Wikipedia and Knowledge Graph lookups are wired in.

## Credits

The app code and the conversation template come from [FacebookMessengerBot](https://github.com/ahmadfaizalbh/FacebookMessengerBot) by Ahmad Faizal B H. The conversation engine is [chatbotAI](https://github.com/ahmadfaizalbh/Chatbot) and [django-chatbot](https://github.com/ahmadfaizalbh/django-chatbot) by the same author.

Changes in this repository:

- Standard Django layout (`fbbot/` project, `bot/` app)
- Secret key, tokens and API key read from environment variables instead of `settings.py`
- Webhook skips echoes and non-text messages, handles failed Facebook and Google API calls, and trims replies to the Messenger length limit
- `re_path` URL config and a basic home page
- chatbotAI and django-chatbot versions that work together, plus migrations for the django-chatbot tables
- "What is my name?" now reaches the name reply instead of the Wikipedia lookup

## License

The original project does not include a license, so this repository does not add one.
