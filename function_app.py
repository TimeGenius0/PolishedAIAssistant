import azure.functions as func
import logging
import os
import random
import json
from azure.cosmos import CosmosClient, exceptions
import pdb
import uuid
from datasets_ import fetch_datapoints, send_datapoints_bubble
from chat import call_chat_endpoint
import pandas as pd

# Initialize Cosmos DB client
cosmosdb_endpoint = os.environ['CosmosDBEndpoint']
cosmosdb_key = os.environ['CosmosDBKey']
cosmosdb_database_name = 'ToDoList'
cosmosdb_container_name = 'Items'
cosmosdb_container_datapoints = 'Datapoints'
cosmosdb_datasets='Datasets'
client = CosmosClient(cosmosdb_endpoint, cosmosdb_key)
database = client.get_database_client(cosmosdb_database_name)
container = database.get_container_client(cosmosdb_container_name)
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
@app.route(route="data")
def data(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Create_dataset HTTP trigger function processed a request.')
    try:
        req_body = req.get_json()
        user_id = req_body.get('user_id')
        scenario_id = req_body.get('scenario_id')
        request = req_body.get('request')
    except ValueError:
        message = req.params.get('message')
    #pdb.set_trace()
    sucess=False
    logging.info('request received.'+request)
    if request:
        datapoints=fetch_datapoints(request)
        logging.info('Datapoints fetched.'+str(datapoints))
        dataset={"dataset_name":request,"dataset_origin":request,"dataset_description":request, "dataset_id":str(uuid.uuid4())}
        success=store_datapoints(datapoints,dataset,user_id,scenario_id)
        logging.info('Datapoints stored.')
        bubble_response=send_datapoints_bubble(datapoints,dataset,user_id,scenario_id)
        logging.info('Datapoints sent to bubble.')
    if bubble_response.status_code == 200:
        return func.HttpResponse(json.dumps(datapoints),status_code=200)
    else:
        return func.HttpResponse(
             "Error - No datapoints found or stored.",
             status_code=400
        ) 
def store_datapoints(data,dataset,user_email="",scenario_id="",model_id=""):
        try:
            database = client.get_database_client(cosmosdb_database_name)
        except exceptions.CosmosResourceNotFoundError:
            logging.error(f"Database '{cosmosdb_database_name}' not found.")
        try:
            container = database.get_container_client(cosmosdb_container_datapoints)
        except exceptions.CosmosResourceNotFoundError:
            logging.error(f"Container '{cosmosdb_container_name}' not found.")
        for datapoint in data:
            datapoint["scenario_id"]=scenario_id
            datapoint["user_email"]=user_email
            datapoint["model_id"]=model_id
            datapoint["dataset_id"]=dataset["dataset_id"]
            datapoint["dataset_name"] =dataset["dataset_name"]
            datapoint["dataset_origin"] =dataset["dataset_origin"]
            datapoint["dataset_name"] =dataset["dataset_name"]
            try:
                pdb.set_trace()
                container.create_item(body=datapoint)
                
            except exceptions.CosmosHttpResponseError as e:
                logging.error(f"Failed to store item in database: {e.message}")
                raise
@app.route(route="AiChat")
def AiChat(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        req_body = req.get_json()
        user_id = req_body.get('user_id')
        message = req_body.get('message')
    except ValueError:
        message = req.params.get('message')
    #pdb.set_trace()
    if message:
        # Call OpenAI API
        message_response = call_chat_endpoint(message,user_id)
        # Store message and response in database
        store_message_in_database(message, message_response,user_id)
        # Return OpenAI response
        return func.HttpResponse(message_response, status_code=200)
    else:
        return func.HttpResponse(
             "Please provide a 'message' parameter in the request body or query string.",
             status_code=400
        )
def store_message_in_database(message, response,user_id):
    item = {
        'message': message,
        'response': response,
        'id': str(random.randint(111111111, 1000000000000)),
        'user_id': user_id
    }
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
        container.create_item(body=item)
        #pdb.set_trace()
    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Failed to store item in database: {e.message}")
        raise

def create_points_lists(df,result):
    # Initialize the main points list
    points_list = []
    # Create the main points list
    for _, row in df.iterrows():
        point = {'input': row['INPUT'], 'output': row['OUTPUT'],'ground_truth':row['Ground_truth']}
        points_list.append(point)
    # Initialize dictionaries to hold positive and negative lists for each boolean column
    # Iterate through each column in the dataframe
    for column in df.columns:
        if df[column].dtype == bool:
            positive_list = []
            negative_list = []
            # Iterate through each row in the dataframe
            for _, row in df.iterrows():
                point = {'input': row['INPUT'], 'output': row['OUTPUT'],'ground_truth':row['Ground_truth']}
                # Append to the respective list based on the boolean value
                if row[column]:
                    positive_list.append(point)
                else:
                    negative_list.append(point)
            # Store the lists in the dictionary
            result[f'positive_{column}'] = positive_list
            result[f'negative_{column}'] = negative_list
            result["all data"] = points_list
            #pdb.set_trace()
    return points_list, result
# Function to create lists based on quartiles

def create_quartile_lists(df,result):
    # Initialize the main points list
    points_list = []
    # Create the main points list
    for _, row in df.iterrows():
        point = {'input': row['INPUT'], 'output': row['OUTPUT'],'ground_truth':row['Ground_truth']}
        points_list.append(point)
    # Initialize dictionary to hold quartile lists for each numerical column
    # Iterate through each column in the dataframe
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]) and not pd.api.types.is_bool_dtype(df[column]) and "eval" not in column and "model" not in column and "ground_truth" not in column:
            # Calculate quartiles
            quartiles = df[column].quantile([0.25, 0.5, 0.75])
            # Initialize lists for each quartile
            top_quartile = []
            second_quartile = []
            third_quartile = []
            bottom_quartile = []
            # Iterate through each row in the dataframe
            for _, row in df.iterrows():
                point = {'input': row['INPUT'], 'output': row['OUTPUT'],'ground_truth':row['Ground_truth']}
                # Append to the respective quartile list based on the column value
                if row[column] > quartiles[0.75]:
                    top_quartile.append(point)
                elif row[column] > quartiles[0.5]:
                    second_quartile.append(point)
                elif row[column] > quartiles[0.25]:
                    third_quartile.append(point)
                else:
                    bottom_quartile.append(point)
                #pdb.set_trace()
            # Store the lists in the dictionary
            result[f'top_quartile_{column}'] = top_quartile
            result[f'second_quartile_{column}'] = second_quartile
            result[f'third_quartile_{column}'] = third_quartile
            result[f'bottom_quartile_{column}'] = bottom_quartile
    return points_list

'''
@app.blob_trigger(arg_name="myblob", path="csvfile",connection="csvstorage") 
def csv_file(myblob: func.InputStream):
    result_quartile={}
    result_boolean={}
    df = pd.read_csv(myblob)
    create_quartile_lists(df,result_quartile)
    create_points_lists(df,result_boolean)
    model_id=df.iloc[0, 0]
    user_email=df.iloc[1, 0]
    #logging.info(f"Quartile lists are {result_quartile}")
    #logging.info(f"Category lists are {result_boolean}")
    for parameter, datapoints in result_quartile.items():
        dataset={"dataset_id":str(uuid.uuid4()),"dataset_name":parameter,"dataset_description":parameter,"dataset_origin":"model_data"}
        logging.info(f"starting to process {dataset['dataset_name']} in result quartile" )
        dataset_bubble=[]
        for item in datapoints:
            datapoint= {
            'input_text': item["input"],
            'input_url':  "",
            'output_text':  "",
            'output_url':  item["output"],
            "ground_truth": item["ground_truth"],
            'model_id': model_id,
            'user_email': user_email,
            'scenario_id': "",
            'id':str(uuid.uuid4())+str(uuid.uuid4())
            }
            dataset_bubble.append(datapoint)
        store_datapoints(dataset_bubble,dataset,user_email,"",model_id)
        send_datapoints_bubble(dataset_bubble,dataset,user_email,"",model_id)

        '''