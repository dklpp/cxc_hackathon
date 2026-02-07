from dotenv import load_dotenv
from flask import Flask, send_file

load_dotenv()

app = Flask(__name__)

@app.route('/voice.xml')
def voice():
    return send_file('voice.xml', mimetype='text/xml')

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    print("Voice.xml available at: http://localhost:5000/voice.xml")
    app.run(host='0.0.0.0', port=5000, debug=True)