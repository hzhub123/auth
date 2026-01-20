import os
from flask import Flask, session, redirect, request
from requests_oauthlib import OAuth2Session

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

CLIENT_ID = os.environ["OAUTH2_CLIENT_ID"]
CLIENT_SECRET = os.environ["OAUTH2_CLIENT_SECRET"]

# ⚠️ TROQUE pela URL do Render
REDIRECT_URI = "https://auth-9801.onrender.com/callback"


API_BASE = "https://discord.com/api"
AUTH_URL = API_BASE + "/oauth2/authorize"
TOKEN_URL = API_BASE + "/oauth2/token"

SCOPES = ["identify"]

# Simples "banco" em memória (para teste)
verified_users = set()

def make_session(token=None, state=None):
    return OAuth2Session(
        CLIENT_ID,
        token=token,
        state=state,
        scope=SCOPES,
        redirect_uri=REDIRECT_URI
    )

@app.route("/")
def login():
    discord = make_session()
    auth_url, state = discord.authorization_url(AUTH_URL)
    session["oauth_state"] = state
    return redirect(auth_url)

@app.route("/callback")
def callback():
    discord = make_session(state=session["oauth_state"])
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=CLIENT_SECRET,
        authorization_response=request.url
    )

    user = discord.get(API_BASE + "/users/@me").json()
    user_id = int(user["id"])

    # Marca como verificado
    verified_users.add(user_id)

    return "✅ Verificação concluída! Volte ao Discord."

@app.route("/is_verified/<int:user_id>")
def is_verified(user_id):
    return {"verified": user_id in verified_users}

