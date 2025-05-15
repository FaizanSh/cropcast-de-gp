#!/usr/bin/python
# import boto3 # For AWS SDK
import traceback # For detailed error logging
import os  # For running cmd
import sys  # For exiting code
import yaml  # To read YAML config file
import logging  # For python logger
import json  # To parse JSON tags to S3
from airflow.models import Variable
from airflow import configuration
import urllib
import datetime

from utils.teams_webhook import TeamsWebhook

def get_webhook_value(variableName):
    try:
        envName=Variable.get('ENVIRONMENT')
        return Variable.get(envName +"-" + variableName)
    except Exception as e:  
       return("")

def send_teams_notification(webhook_url,payload):
    try:
        logging.info(f'Using Webhook {webhook_url}')

        teams = TeamsWebhook(webhook_url)
        
        teams.send_message_card(payload)

        logging.info('Message Delivered!')
    except Exception as e:

        print("Error publishing to SNS Topic")
        print ('-'*60)
        traceback.print_exc()
        print ('-'*60)
        sys.exit()


#This section of the code is called when the DAG results in a Failiure
def notify_fail(context):

    task_id      = context["task"].task_id
    task_instance= context["task_instance"]
    dag_id      = context["dag"].dag_id
    project     = dag_id.split("_")[0]
    today       = datetime.datetime.now() #.strftime ("%m/%d/%Y")
    due_date    = today + datetime.timedelta(days=3)
    exception   = context["exception"]

    execution_date = task_instance.execution_date.isoformat()
    encoded_execution_date = urllib.parse.quote_plus(execution_date)

    base_url = configuration.get('webserver', 'BASE_URL')
    dag_url = base_url+'/dags/'+'{dag_name}/grid'.format(dag_name = dag_id)
    log_url = base_url+'/log?dag_id='+'{dag_name}&task_id={task_name}&execution_date={date}'.format(dag_name = dag_id, task_name = task_id, date = encoded_execution_date)

    note        = ''
    note        += '\n\nPlease acknowledge this message and add details about the progress in reply'
    note        += '\n\n[This is an auto-generated Notification]'

    payload = {
        "type": "message",
        "attachments": [
            {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.2",
                "body": [
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": "Airflow : Failure Alert",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": f"{project}",
                    "isSubtle": True,
                    "wrap": True
                },
                {
                    "type": "Image",
                    "url": "https://static-00.iconduck.com/assets.00/airflow-icon-512x512-tpr318yf.png",
                    "size": "Small",
                    "style": "Person"
                },
                {
                    "type": "FactSet",
                    "facts": [
                    {
                        "title": "DAG ID:",
                        "value": f"{dag_id}"
                    },
                    {
                        "title": "Task Name:",
                        "value": f"{task_id}"
                    },
                    {
                        "title": "Time:",
                        "value": f"{today}"
                    },
                    {
                        "title": "Exception:",
                        "value": f"{exception}"
                    },
                    {
                        "title": "Note:",
                        "value": f"{note}"
                    }
                    ]
                }
                ],
                "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "Logs URL",
                    "url": f"{log_url}"
                },
                {
                    "type": "Action.OpenUrl",
                    "title": "DAG URL",
                    "url": f"{dag_url}"
                }
                ]
            }
            }
        ]
        }


    send_teams_notification(webhook_url=get_webhook_value(project),payload=payload)

def notify_failure_processing(function_name, value, qualifier, result, context):

    task_id      = context["task"].task_id
    task_instance= context["task_instance"]
    dag_id      = context["dag"].dag_id
    project     = dag_id.split("_")[0]
    today       = datetime.datetime.now() #.strftime ("%m/%d/%Y")
    due_date    = today + datetime.timedelta(days=3)

    execution_date = task_instance.execution_date.isoformat()
    encoded_execution_date = urllib.parse.quote_plus(execution_date)

    base_url = configuration.get('webserver', 'BASE_URL')
    dag_url = base_url+'/dags/'+'{dag_name}/grid'.format(dag_name = dag_id)
    log_url = base_url+'/log?dag_id='+'{dag_name}&task_id={task_name}&execution_date={date}'.format(dag_name = dag_id, task_name = task_id, date = encoded_execution_date)

    note        = ''
    note        += '\n\nPlease acknowledge this message and add details about the progress in reply'
    note        += '\n\n[This is an auto-generated Notification]'

    payload = {
    "type": "message",
    "attachments": [
        {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.2",
            "body": [
            {
                "type": "TextBlock",
                "size": "Medium",
                "weight": "Bolder",
                "text": "Airflow : Failure Alert",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": f"{project}",
                "isSubtle": True,
                "wrap": True
            },
            {
                "type": "Image",
                "url": "https://static-00.iconduck.com/assets.00/airflow-icon-512x512-tpr318yf.png",
                "size": "Small",
                "style": "Person"
            },
            {
                "type": "FactSet",
                "facts": [
                {
                    "title": "DAG ID:",
                    "value": f"{dag_id}"
                },
                {
                    "title": "Task Name:",
                    "value": f"{task_id}"
                },
                {
                    "title": "Function Name:",
                    "value": f"{function_name}:${qualifier}"
                },
                {
                    "title": "Time:",
                    "value": f"{today}"
                },
                {
                    "title": "Function Input:",
                    "value": f"{value}"
                },
                {
                    "title": "Failure Details:",
                    "value": f"{result}"
                },
                {
                    "title": "Note:",
                    "value": f"{note}"
                }
                ]
            }
            ],
            "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "Logs URL",
                "url": f"{log_url}"
            },
            {
                "type": "Action.OpenUrl",
                "title": "DAG URL",
                "url": f"{dag_url}"
            }
            ]
        }
        }
    ]
    }


    send_teams_notification(webhook_url=get_webhook_value(project),payload=payload)



