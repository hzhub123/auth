from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Site online com sucesso!"

if __name__ == "__main__":
    app.run()
