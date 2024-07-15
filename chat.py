import os
import requests
import logging
import os
from azure.cosmos import CosmosClient, exceptions

cosmosdb_endpoint = os.environ['CosmosDBEndpoint']
cosmosdb_key = os.environ['CosmosDBKey']
cosmosdb_database_name = 'ToDoList'
cosmosdb_container_name = 'Items'
cosmosdb_container_datapoints = 'Datapoints'
client = CosmosClient(cosmosdb_endpoint, cosmosdb_key)
database = client.get_database_client(cosmosdb_database_name)
container = database.get_container_client(cosmosdb_container_name)

def call_chat_endpoint(message,user_id):
    openai_api_key = os.environ['OpenAIKey']
    items= fetch_messages_from_database(user_id)
    
    messages= [{"role": "system", "content": "You are a helpful assistant."}]
    for item in items:
        messages.append({"role":"user","content":item["message"]}) 
        messages.append({"role":"system","content":item["response"]})
    messages.append({"role":"user","content":message})
    
    headers = {
        'Authorization': f'Bearer {openai_api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-3.5-turbo',  # Use the appropriate model
        'messages': messages,
        'max_tokens': 100
    }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    
    response_data = response.json()
    #pdb.set_trace()
    return response_data['choices'][0]['message']['content']

def fetch_messages_from_database(user_id):

    #pdb.set_trace()  # Remove or comment out if not needed for debugging
    
    try:
        database = client.get_database_client(cosmosdb_database_name)
    except exceptions.CosmosResourceNotFoundError:
        logging.error(f"Database '{cosmosdb_database_name}' not found.")
    
    try:
        container = database.get_container_client(cosmosdb_container_name)
    except exceptions.CosmosResourceNotFoundError:
        logging.error(f"Container '{cosmosdb_container_name}' not found.")
    
    try:
        # Define the query
        query = f"SELECT * FROM c WHERE c.user_id = '{user_id}' ORDER BY c.creation_date DESC"

        # Execute the query
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Failed to store item in database: {e.message}")
        raise
    
    # pdb.set_trace()
    return items