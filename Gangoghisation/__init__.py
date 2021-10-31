import logging
import requests
import azure.functions as func
import uuid
import logging
import os
import json
import base64
import hmac
import hashlib
import urllib.parse
import random
import time
from datetime import datetime, timedelta

_AZURE_STORAGE_CONN_STRING_ENV_NAME = "AzureWebJobsStorage"
_SAS_TOKEN_DEFAULT_TTL = 1
_AZURE_STORAGE_API_VERSION = "2018-03-28"

connString = os.environ[_AZURE_STORAGE_CONN_STRING_ENV_NAME]

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    urlimg = req.params.get('url_imgsrc')
    if not urlimg:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            urlimg = req_body.get('url_imgsrc')

    if urlimg:
        filename=str(uuid.uuid4()).replace("-","")+".jpg"
        jsontosend={
            "url_imgsrc":urlimg,
            "initImage":filename,
            "phrase":"a portrait painting by van gogh",
            "model":"wikiart",
            "iterations":25,
            "size":[500, 500]
        }

        resp = requests.post(os.environ["urlapi"]+"?code="+os.environ["apikey"],
        json=jsontosend)
        ret=""
        if(resp.ok):

            newurl = simplegen_sas_token(filename)["url"]
            ret=newurl
        else:
            ret=resp.reason
        return func.HttpResponse(body=ret,status_code=resp.status_code)
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a url_imgsrc in the query string or in the request body for a personalized response.",
             status_code=200
        )

def simplegen_sas_token(name):
    
    storage_account = None
    storage_key = None

    ll = connString.split(';')
    for l in ll:
        ss = l.split('=',1)
        if len(ss) != 2:
            continue
        if ss[0] == 'AccountName':
           storage_account = ss[1] 
        if ss[0] == 'AccountKey':
           storage_key = ss[1] 
 

    permission = 'rl'
    container_name = "gangoghdemo"
    
    token_ttl = _SAS_TOKEN_DEFAULT_TTL
    return  generate_sas_token(storage_account,storage_key,permission,token_ttl,container_name,name)




def generate_sas_token (storage_account, storage_key, permission, token_ttl, container_name, blob_name = None ):
    sp = permission
    # Set start time to five minutes ago to avoid clock skew.
    st= str((datetime.utcnow() - timedelta(minutes=5) ).strftime("%Y-%m-%dT%H:%M:%SZ"))
    se= str((datetime.utcnow() + timedelta(hours=token_ttl)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    srt = 'o' if blob_name else 'co'

    # Construct input value
    inputvalue = "{0}\n{1}\n{2}\n{3}\n{4}\n{5}\n{6}\n{7}\n{8}\n".format(
        storage_account,  # 0. account name
        sp,                   # 1. signed permission (sp)
        'b',                  # 2. signed service (ss)
        srt,                  # 3. signed resource type (srt)
        st,                   # 4. signed start time (st)
        se,                   # 5. signed expire time (se)
        '',                   # 6. signed ip
        'https',              # 7. signed protocol
        _AZURE_STORAGE_API_VERSION)  # 8. signed version

    # Create base64 encoded signature
    hash =hmac.new(
            base64.b64decode(storage_key),
            inputvalue.encode(encoding='utf-8'),
            hashlib.sha256
        ).digest()

    sig = base64.b64encode(hash)

    querystring = {
        'sv':  _AZURE_STORAGE_API_VERSION,
        'ss':  'b',
        'srt': srt,
        'sp': sp,
        'se': se,
        'st': st,
        'spr': 'https',
        'sig': sig,
    }
    sastoken = urllib.parse.urlencode(querystring)

    sas_url = None
    if blob_name:
        sas_url = "https://{0}.blob.core.windows.net/{1}/{2}?{3}".format(
            storage_account,
            container_name,
            blob_name,
            sastoken)
    else:
        sas_url = "https://{0}.blob.core.windows.net/{1}?{2}".format(
            storage_account,
            container_name,
            sastoken)

    return {
            'token': sastoken,
            'url' : sas_url
           }
