import os
import requests
from flask import Flask, session, redirect, request
from requests_oauthlib import OAuth2Session

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

CLIENT_ID = os.environ["OAUTH2_CLIENT_ID"]
CLIENT_SECRET = os.environ["OAUTH2_CLIENT_SECRET"]
BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

REDIRECT_URI = "https://auth-9801.onrender.com/callback"

API_BASE = "https://discord.com/api"
AUTH_URL = API_BASE + "/oauth2/authorize"
TOKEN_URL = API_BASE + "/oauth2/token"

# Scopes do OAuth
SCOPES = ["identify"]

# Servidores alvo
TARGET_GUILDS = [
    1436831609189040161,  # Servidor 1
    1457835488902905869,  # Servidor 2
]

# ID do cargo a ser dado (substitua pelo real)
ROLE_ID = 123456789012345678  # ⚠️ coloque o ID real do cargo

# "Banco" simples em memória
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
    try:
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

        # Dar cargo em todos os servidores
        headers = {
            "Authorization": f"Bot {BOT_TOKEN}",
            "Content-Type": "application/json"
        }

        for guild_id in TARGET_GUILDS:
            url = f"{API_BASE}/guilds/{guild_id}/members/{user_id}/roles/{ROLE_ID}"
            response = requests.put(url, headers=headers)
            if response.status_code == 204:
                print(f"Cargo dado com sucesso ao usuário {user_id} no servidor {guild_id}")
            else:
                print(f"Erro ao dar cargo {ROLE_ID} ao usuário {user_id} no servidor {guild_id}: {response.text}")

        return "✅ Verificação concluída! Você já recebeu o cargo no Discord."

    except Exception as e:
        print("Erro no callback:", e)
        return "❌ Ocorreu um erro durante a verificação."


@app.route("/is_verified/<int:user_id>")
def is_verified(user_id):
    return {"verified": user_id in verified_users}


if __name__ == "__main__":
    # Para testes locais
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
