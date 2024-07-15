import uuid
import azure.functions as func
import logging
import requests
import os
import random
import json
from azure.cosmos import CosmosClient, exceptions
import pdb



def fetch_datapoints(request):
    datapoints=[
        {
        'input_text': "new",
        'input_url':  "new",
        'output_text':  "new",
        'output_url':  "new",
        'model':  "new",
        'id':str(uuid.uuid4())+str(uuid.uuid4()),
        'backend_dataset_id':"gjkuhuiuiiiuuiiuiuui12323",
        'dataset_name':"dataset_name",
        'dataset_origin':"dataset_name",
        'dataset_description':"dataset_description",
        "ground_truth":"ground truth"
        }
        ]
    return datapoints

def send_datapoints_bubble(datapoints,dataset,user_email,scenario_id,model_id=""):
    response= None
    bubble_key = os.environ['bubble_api_key']
    headers = {
        "Authorization": "Bearer "+ bubble_key,
        'Content-Type':'application/json'
    }
    bubble_workflow_datapoint=os.environ['bubble_workflow_endpoint']
    for datapoint in datapoints:

        data = {'input_text': datapoint["input_text"],
                'input_url': datapoint["input_url"],
                'output_text': datapoint["output_text"],
                'output_url': datapoint["output_url"],
                'model': model_id,
                'ground_truth':datapoint["ground_truth"],
                'backend_dp_id':datapoint["id"],
                'backend_user_email': user_email,
                'backend_scenario_id':scenario_id,
                'backend_dataset_id':dataset["dataset_id"],
                'dataset_name':dataset["dataset_name"],
                'dataset_origin':dataset["dataset_origin"],
                'dataset_description':dataset["dataset_description"],
            }
        #pdb.set_trace()
        response = requests.post(bubble_workflow_datapoint+"create_datapoints", headers=headers, json=data)
    return response
