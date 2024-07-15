import azure.functions as func
import logging
import requests
import os
from azure.cosmos import CosmosClient

# Initialize Cosmos DB client
cosmosdb_endpoint = os.environ['CosmosDBEndpoint']
cosmosdb_key = os.environ['CosmosDBKey']
cosmosdb_database_name = 'ToDoList'
cosmosdb_container_name = 'Item'

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

client = CosmosClient(cosmosdb_endpoint, cosmosdb_key)
database = client.get_database_client(cosmosdb_database_name)
container = database.get_container_client(cosmosdb_container_name)

def call_openai_api(message):
    openai_api_key = os.environ['OpenAIKey']
    headers = {
        'Authorization': f'Bearer {openai_api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': message,
        'max_tokens': 150
    }
    response = requests.post('https://api.openai.com/v1/engines/davinci-codex/completions', headers=headers, json=data)
    return response.json()['choices'][0]['text']

def store_message_in_database(message, response):
    item = {
        'message': message,
        'response': response
    }
    container.create_item(body=item)

@app.route(route="AiChat")
def AiChat(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        message = req_body.get('message')
    except ValueError:
        message = req.params.get('message')

    if message:
        # Call OpenAI API
        openai_response = call_openai_api(message)
        
        # Store message and response in database
        store_message_in_database(message, openai_response)
        
        # Return OpenAI response
        return func.HttpResponse(openai_response, status_code=200)
    else:
        return func.HttpResponse(
             "Please provide a 'message' parameter in the request body or query string.",
             status_code=400
        )
