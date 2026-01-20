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

# 1. ADICIONADO: Scope "guilds.join" para permitir entrar em servidores
SCOPES = ["identify", "guilds.join"]

TARGET_GUILDS = [
    1436831609189040161,  # Servidor 1
    1457835488902905869,  # Servidor 2
]

ROLE_ID = 1463059819811438801  

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
        discord = make_session(state=session.get("oauth_state"))
        token = discord.fetch_token(
            TOKEN_URL,
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )

        user = discord.get(API_BASE + "/users/@me").json()
        user_id = user["id"]
        access_token = token["access_token"] # Token do usuário para autorizar a entrada

        # Cabeçalho para o Bot (usado para adicionar o membro)
        bot_headers = {
            "Authorization": f"Bot {BOT_TOKEN}",
            "Content-Type": "application/json"
        }

        for guild_id in TARGET_GUILDS:
            # 2. LÓGICA PARA ADICIONAR O USUÁRIO AO SERVIDOR
            join_url = f"{API_BASE}/guilds/{guild_id}/members/{user_id}"
            
            # Dados necessários: o access_token que o usuário nos deu ao autorizar
            join_data = {
                "access_token": access_token,
                "roles": [str(ROLE_ID)] # Adiciona o cargo opcionalmente já na entrada
            }

            response = requests.put(join_url, headers=bot_headers, json=join_data)

            if response.status_code == 201:
                print(f"Usuário {user_id} entrou e recebeu cargo no servidor {guild_id}")
            elif response.status_code == 204:
                print(f"Usuário {user_id} já estava no servidor. Tentando dar cargo...")
                # Se ele já estava lá, apenas tentamos dar o cargo separadamente
                role_url = f"{API_BASE}/guilds/{guild_id}/members/{user_id}/roles/{ROLE_ID}"
                requests.put(role_url, headers=bot_headers)
            else:
                print(f"Erro no servidor {guild_id}: {response.text}")

        verified_users.add(int(user_id))
        return "✅ Verificação concluída! cargo adicionado."

    except Exception as e:
        print("Erro no callback:", e)
        return "❌ Ocorreu um erro durante a verificação."

@app.route("/is_verified/<int:user_id>")
def is_verified(user_id):
    return {"verified": user_id in verified_users}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

