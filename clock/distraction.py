import openai
from dotenv import load_dotenv
import os

class DetectDistraction:
    
    def __init__(self):
        load_dotenv()  # Automatically finds the .env file
        self.api_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = self.api_key
        
    def classify(self, app_name):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
            {"role": "system", "content": "Respond with one of two words, PRODUCTIVE and NONPRODUCTIVE depending on the application provided, for example programming IDE's are PRODUCTIVE."},
            {"role": "user", "content": f"Application name: {app_name}\nResponse:"}
            ],
            max_tokens=10,  # Increased max_tokens to capture the full response
            n=1,
            stop=None,
            temperature=0
        )

        return response.choices[0].message['content'].strip()