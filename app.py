from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Initialize Flask application
app = Flask(__name__)

# Load the system prompt
try:
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
    print("Loaded system prompt.")
except Exception as e:
    print(f"Error loading system prompt: {e}")
    SYSTEM_PROMPT = "You are an AI assistant designed to simulate conversations with loved ones."

# Define a global dictionary to store user histories
user_histories = {}
MAX_HISTORY_LENGTH = 30  # Limit the number of messages stored per user

def limit_user_history(history):
    """Keep user history within limits, retaining the system prompt."""
    return [history[0]] + history[1:][-MAX_HISTORY_LENGTH:]

@app.route('/webhook', methods=['POST'])
def webhook():
    form_data = request.form

    # Extract user information
    sender = form_data.get("From", "")
    incoming_message = form_data.get("Body", "").strip()

    # Check if this is a first-time user
    if sender not in user_histories:
        user_histories[sender] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Append user's message to history
    user_histories[sender].append({"role": "user", "content": incoming_message})

    # Generate AI response
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=user_histories[sender]
        )
        bot_reply = response.choices[0].message.content.strip()
        user_histories[sender].append({"role": "assistant", "content": bot_reply})
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        bot_reply = "Sorry, I couldn't process your request. Please try again later."

    # Create a Twilio response
    twilio_response = MessagingResponse()
    twilio_response.message(bot_reply)
    return str(twilio_response)

@app.route('/')
def home():
    return "Welcome to the After Live Chatbot API. This service is running!"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)