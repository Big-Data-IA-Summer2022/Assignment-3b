import requests
import json
import os
import sys
from PIL import Image
import os, os.path
import io
from google.cloud import bigquery
import logging
import shutil
import time
from pprint import pprint

import pendulum

from airflow import DAG
from airflow.decorators import task
from airflow.operators.python_operator import PythonOperator



pathok='dags/casting_data/test/ok_front'
pathdef ='dags/casting_data/test/def_front'

#pathdef = r"C:\Users\abhij\Downloads\archive\casting_data\casting_data\test\def_front"
#pathok = r"C:\Users\abhij\Downloads\archive\casting_data\casting_data\test\ok_front"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] =  'dags/key.json'


urlp = 'https://damg7245-assignment03-api-xd232aklcq-uc.a.run.app/predict_with_augmented_data_trained_model'

def login():
    url = "https://damg7245-assignment03-api-xd232aklcq-uc.a.run.app/login"
    payload={'username': 'kunjiraman.a@northeastern.edu', 'password': 'ucbp2QYV4bs'}
    response = requests.request("POST", url, data=payload)
    if response.status_code == 200:
        json_data = json.loads(response.text)
        print('login successful')
        print(json_data["access_token"])
        return json_data


def populatetable(actual: str, predicted: str):
    client = bigquery.Client()
    rows_to_insert =[{"actual":actual, "predicted":predicted}]
    errors = client.insert_rows_json('defect-detection-356414.for_logs.confusion-matrix', rows_to_insert)  # Make an API request.
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))

default_args = {
    'owner': 'airflow',
    'concurrency': 1,
    'retries': 0,
    'depends_on_past': False
}

def validate():
    urlp = 'https://damg7245-assignment03-api-xd232aklcq-uc.a.run.app/predict_with_augmented_data_trained_model'
    json_data=login()
    for i in os.listdir(pathok):
        i=os.path.join(pathok,i)
        im = Image.open(i)
        im_resize = im.resize((300, 300))
        buf = io.BytesIO()
        im_resize.save(buf, format='JPEG')
        byte_im = buf.getvalue()
        headers = {}
        headers['Authorization'] = "Bearer " + json_data["access_token"]
        response = requests.request("POST", url=urlp, files={'file': byte_im}, headers=headers)
        text=response.text
        print(text)
        if response.status_code == 200:
            if text == '"defect"':
                text='defect'
            elif text=='"ok"':
                text='ok'
        actual='ok'
        predicted=text
        populatetable(actual, predicted)
    for i in os.listdir(pathdef):
        i=os.path.join(pathdef,i)
        im = Image.open(i)
        im_resize = im.resize((300, 300))
        buf = io.BytesIO()
        im_resize.save(buf, format='JPEG')
        byte_im = buf.getvalue()
        headers = {}
        headers['Authorization'] = "Bearer " + json_data["access_token"]
        response = requests.request("POST", url=urlp, files={'file': byte_im}, headers=headers)
        text=response.text
        print(text)
        if response.status_code == 200:
            if text == '"defect"':
                text='defect'
            elif text=='"ok"':
                text='ok'
        actual='defect'
        predicted=text
        populatetable(actual, predicted)
with DAG(
    dag_id='Validating-test-data',
    schedule_interval=None,
    start_date=pendulum.datetime(2022, 7, 22, tz="UTC"),
    catchup=False,
    tags=['validate']
) as dag:
    t0_start= PythonOperator(task_id='UploadModels',python_callable=validate)
t0_start

    
