import logging
import azure.functions as func
import requests
import openai

# OpenAI API key
OPENAI_API_KEY = 'your-openai-api-key'

# Bubble.io endpoint URL
BUBBLE_IO_ENDPOINT = 'https://bubble.io/app/your-endpoint'

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Parse the request JSON body
        req_body = req.get_json()
        messages = req_body.get('messages')

        if not messages:
            return func.HttpResponse(
                "Please pass a list of messages in the request body",
                status_code=400
            )

        # Process each message
        responses = []
        for message in messages:
            # Send message to OpenAI API
            openai_response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=message,
                max_tokens=150
            )

            # Extract the text response
            reply = openai_response.choices[0].text.strip()
            responses.append(reply)

            # Post reply to Bubble.io
            bubble_response = requests.post(
                BUBBLE_IO_ENDPOINT,
                json={"reply": reply}
            )

            if bubble_response.status_code != 200:
                logging.error(f"Failed to post to Bubble.io: {bubble_response.text}")

        return func.HttpResponse(
            "Messages processed successfully",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return func.HttpResponse(
            "Internal server error",
            status_code=500
        )
