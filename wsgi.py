from bot import app
from flask import Flask, request

flask_app = Flask(__name__)

@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(await request.get_json(), app.bot)
    await app.process_update(update)
    return '', 200

if __name__ == '__main__':
    flask_app.run()
