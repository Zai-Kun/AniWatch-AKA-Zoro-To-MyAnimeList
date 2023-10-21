# No, I didn't use ChatGPT here. 😄

'''
Instructions:


Authenticate and Generate Tokens:

    1. Go to the "Token Manager" page by clicking on the "Token Manager" button in the navigation menu.
    2. Click on the "Get Token" button to authenticate with MyAnimeList.
    3. You will be redirected to the MyAnimeList website to authorize the app.
    4. After authorization, you will be redirected back to the app where you can copy your access token and refresh token

NOTE: Remember to save your token and refresh token in a secure place.

Check Token:

    1. Go to the "Token Manager" page by clicking on the "Token Manager" button in the navigation menu.
    2. Click the "Check token" button
    3. A prompt will appear asking you to enter your token.
    4. Enter the token and click "OK."
    5. Another prompt will appear, indicating whether your token is still valid or has expired.

Refresh Token:

    1. Go to the "Token Manager" page by clicking on the "Token Manager" button in the navigation menu.
    2. Click the "Refresh token" button.
    3. A prompt will appear asking you to enter your refresh token.
    4. Enter the refresh token and click "OK."
    5. If your refresh token is valid, you will be redirected to a page where you can copy your new token and refresh token.

NOTE: Remember to save your token and refresh token in a secure place.

Export Watchlist to MyAnimeList:

    1. Go to the "Zoro to MAL" page by clicking on the "Zoro to MyAnimelist" button in the navigation menu.
    2. Enter your MyAnimeList access token in the provided text field.
    3. Select a JSON file containing your watchlist data using the file upload field.
    4. Click on the "Upload" button to start the export process.
    5. The app will display a progress indicator, showing the percentage of the watchlist exported.
'''

import base64
import json
import os
import queue
import random
import secrets
import string
from threading import Lock, Thread
from urllib.parse import urlencode

import discord
import requests
from discord.ext import tasks
from flask import Flask, jsonify, redirect, render_template, request, session
from waitress import serve

client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
url = "https://myanimelist.net/v1/oauth2/token"

intents = discord.Intents.all()
client = discord.Client(intents=intents,
                        status=discord.Status.dnd,
                        activity=discord.Activity(
                            name="Zoro-To-MyAnimeList",
                            type=discord.ActivityType.playing))
USER_AGENTS = queue.Queue()


def get_new_code_verifier() -> str:
    token = secrets.token_urlsafe(100)
    return token[:128]


def TO_PERCENTAGE(value, total_value):
    return str(int((value / total_value) * 100)) + '%'


def GENERATE_ID():
    letters = string.ascii_letters + string.digits
    key = ''.join(random.choice(letters) for _ in range(30))
    return base64.b64encode(key.encode()).decode()


def CHECK_TOKEN(token):
    headers = {
        "Authorization": f"Bearer {str(token)}",
        "Content-Type": "application/json"
    }

    url = "https://api.myanimelist.net/v2/users/@me"

    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        return True
    else:
        return False


def VERIFY_JSON(watchlist_zoro):

    for i in watchlist_zoro.keys():
        for j in watchlist_zoro[i]:
            if not 'link' in j:
                return False

    return True


class PROGRESS_MANAGER:

    def __init__(self):
        self.lock = Lock()
        self.clients = {}

    def CREATE_CLIENT(self):
        with self.lock:
            ID = GENERATE_ID()

            while True:
                if ID not in self.clients:
                    break
                else:
                    ID = GENERATE_ID()

            self.clients[ID] = "0%"

        return ID

    def DELETE_CLIENT(self, ID):
        with self.lock:
            if ID in self.clients:
                del self.clients[ID]

    def GET_CLIENT_PROGRESS(self, ID):
        with self.lock:
            if ID in self.clients:
                return self.clients[ID]
            else:
                return None

    def UPDATE_PROGRESS(self, ID, progress):
        with self.lock:
            if ID in self.clients:
                self.clients[ID] = progress

    def CLIENT_EXISTS(self, ID):
        with self.lock:
            if ID in self.clients:
                return True
            else:
                return False


def EXPORT_TO_MAL(API_KEY, ID, watchlist_zoro):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    convert = {
        'On-Hold': 'on_hold',
        'Completed': 'completed',
        'Plan to watch': 'plan_to_watch',
        'Dropped': 'dropped',
        'Watching': 'watching',
    }

    total_anime = 0
    total_anime_added = 0

    for i in watchlist_zoro.keys():
        total_anime += len(watchlist_zoro[i])

    for i in watchlist_zoro.keys():
        for j in watchlist_zoro[i]:

            anime_id = j["link"].split("/")[-1]
            url = f"https://api.myanimelist.net/v2/anime/{anime_id}/my_list_status"

            payload = {"status": convert[i]}

            if i == 'Completed':
                payload["num_watched_episodes"] = -1

            response = requests.put(url,
                                    headers=headers,
                                    data=urlencode(payload))
            if not response.ok:
                print("Error adding anime to your watchlist:", response.text)
                print(payload)

            total_anime_added += 1
            progress.UPDATE_PROGRESS(
                ID, TO_PERCENTAGE(total_anime_added, total_anime))


progress = PROGRESS_MANAGER()
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)


def MAIN_APP():

    @app.route('/', methods=['HEAD', 'GET'])
    def home():
        if request.method == 'HEAD':
            return ""
        USER_AGENTS.put(request.headers.get('User-Agent'))
        return render_template('index.html')

    @app.route('/gettoken')
    def gettoken():
        if len(request.args) == 0:
            code_verifier = get_new_code_verifier()
            session['code_verifier'] = code_verifier
            return redirect(
                f'https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id={client_id}&code_challenge={code_verifier}&state=RequestID42'
            )
        else:
            code = request.args.get('code')
            code_ver = session.pop('code_verifier', None)
            params = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "code_verifier": code_ver,
                "grant_type": "authorization_code"
            }
            response = requests.post(url, data=params)
            if response.ok:
                script = f'''
                  <script>
                    response = {{
                      "access_token": "{response.json()['access_token']}",
                      "refresh_token": "{response.json()['refresh_token']}"
                    }}
                    function copy(token) {{
                      text = response[token]
                      navigator.clipboard.writeText(text)
                        .then(() => {{
                          alert("Copied to clipboard");
                        }})
                        .catch((err) => {{
                          alert(`Error copying to clipboard: ${{err}}`);
                        }});
                    }}
                  </script>
                  '''
                return render_template("copy.html", script=script)
            else:
                return jsonify({"text": response.text})

    @app.route("/token", methods=['POST'])
    def token():
        data = request.json
        key = list(data.keys())[0]

        if key == "refresh_token":

            refresh_token = data[key]
            url = "https://myanimelist.net/v1/oauth2/token"
            grant_type = "refresh_token"

            payload = {
                "client_id": client_id,
                "grant_type": grant_type,
                "refresh_token": refresh_token,
                "client_secret": client_secret
            }

            if client_secret:
                payload["client_secret"] = client_secret

            response = requests.post(url, data=payload)

            if response.ok:
                return jsonify({
                    "html":
                    render_template("copy.html"),
                    "access_token":
                    response.json()['access_token'],
                    "refresh_token":
                    response.json()['refresh_token']
                })
            else:
                return jsonify({"text": response.text})

        elif key == "check_token":
            token = data[key]

            if CHECK_TOKEN(token):
                return jsonify({"text": "The token has expired."})
            else:
                return jsonify({"text": "The token is still valid."})
        else:
            return jsonify({
                "text":
                "STOP WHATEVER YOU ARE TRYING TO DO AND GO FUCK YOURSELF"
            })

    def not_found(*args):
        return redirect('/')

    @app.route('/tokenmanager')
    def tokenmanager():
        return render_template('tokenmanager.html')

    @app.route('/zorotomal', methods=['GET', 'POST'])
    def zorotomal():
        if request.method == 'POST':
            try:
                zoro_list = json.loads(request.files['file'].read())
                if not VERIFY_JSON(zoro_list):
                    return "Invalid Zoro list file."
            except:
                return "Invalid json file."

            token = request.form['text']

            if CHECK_TOKEN(token):
                return "Invalid MAL token or token has expired."

            ID = progress.CREATE_CLIENT()

            thread = Thread(target=EXPORT_TO_MAL,
                            args=(token, ID, zoro_list),
                            daemon=True)
            thread.start()

            return redirect(f'/zorotomal/{ID}')
        return render_template('zorotomal.html')

    @app.route('/instructions')
    def instructions():
        return render_template('instructions.html')

    @app.route('/zorotomal/<ID>', methods=['GET', 'POST'])
    def return_progress(ID):

        if progress.CLIENT_EXISTS(ID):
            if request.method == 'POST':
                client_progress = progress.GET_CLIENT_PROGRESS(ID)

                if client_progress == "100%":
                    client_progress = "List has been imported to MyAnimeList successfully!!"
                    progress.DELETE_CLIENT(ID)

                return client_progress
            else:
                return render_template('loading.html')
        else:
            return "Invalid ID"

    app.register_error_handler(405, not_found)
    app.register_error_handler(404, not_found)

    serve(app, host="0.0.0.0")


MAIN_APP_THREAD = Thread(target=MAIN_APP, daemon=True)
MAIN_APP_THREAD.start()


@tasks.loop(seconds=0.5)
async def myLoop():
    if not USER_AGENTS.empty():
        USER_AGENT = USER_AGENTS.get()
        channel = client.get_channel(1115764551917518968)
        message = f"Someone visited your web app \:D. User-Agent: **{USER_AGENT}**"
        await channel.send(message)


@client.event
async def on_ready():
    myLoop.start()
    print("started!")


client.run(os.getenv('secret_code'))