import requests
import json
import datetime

class TeamsWebhook:

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url


    def send_message(self, message):
        """
        Send a simple message to the Teams channel.
        """
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "text": message
        }
        response = requests.post(self.webhook_url, headers=headers, data=json.dumps(payload))
        return response.ok


    def send_formatted_message(self, message):
        """
        Send a formatted message to the Teams channel using Markdown.
        """
        formatted_message = f"#### {message}"
        return self.send_message(formatted_message)

    
    def send_message_card(self, card_json):
        """
        Send a MessageCard to the Teams channel.
        """
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.webhook_url, headers=headers, data=json.dumps(card_json))
        return response.ok