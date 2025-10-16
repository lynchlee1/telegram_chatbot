from flask import Flask
import dart_bot  # your existing bot logic

app = Flask(__name__)

@app.route("/")
def index():
    # run your bot code when the service URL is hit
    result = dart_bot.run()  # or whatever your entry function is
    return f"Bot executed successfully: {result}", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)