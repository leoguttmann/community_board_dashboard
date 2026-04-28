import os
import requests
import random
import json
import time
import sys
from PersisterClass import PersisterGlobalVariables
from VoteOptionsEnum import VoteOptions 
import base64
import concurrent.futures

API_KEY = os.environ.get('API_KEY')

# Update with your Lambda URL and Twilio API key
LAMBDA_URL = "https://b9p8ybxhj7.execute-api.us-east-1.amazonaws.com/default/manualentry"
#LAMBDA_URL = "http://127.0.0.1:5000/manualentry"
persister = PersisterGlobalVariables()
persister.load_members()
members = persister.get_members()

def test_send_votes_to_lambda():
    # Start the timer
    max_threads = 50

    # Create a thread pool executor
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        start_time = time.time()

        number_to_send_values = members.keys()

        # Create a list of futures for sending requests
        futures = [executor.submit(send_vote_request, number_to_send,"Yes") for number_to_send in number_to_send_values]

        # Calculate the elapsed time
        elapsed_time = time.time() - start_time
        print('elapsed'+str(elapsed_time))

def send_vote_request(number_sms, vote_to_send):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,  # Add the x-api-key header here
    }
    data = {
            "number_sms": number_sms,
            "vote_to_send": vote_to_send,
    }

    response = requests.post(LAMBDA_URL, headers=headers, data=json.dumps(data))
    # Ensure the response is as expected
    print(str( response.status_code == 200))
    print(response.text)

if __name__ == "__main__":
    #send_vote_request('+19178418243','Yes')
    test_send_votes_to_lambda()
