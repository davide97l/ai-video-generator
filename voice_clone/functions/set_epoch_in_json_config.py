import json
import os
import boto3

s3 = boto3.resource('s3')

def upload_to_aws(filename: str) -> str:
    bucket_name = os.environ.get('bucket_name')
    region = os.environ.get('region')
    session = boto3.Session(
        aws_access_key_id=os.environ.get('access_key_id'),
        aws_secret_access_key=os.environ.get('secret_access_key')
    )
    s3_client = session.client('s3')
    bucket_path = 'voice-clone'
    s3_client.upload_file(f"{filename}", bucket_name, f"{bucket_path}/{filename}")
    s3_base_url = f'https://{bucket_name}.s3.{region}.amazonaws.com/'
    url = f'{s3_base_url}{bucket_path}/{filename}'
    return url

def modify_epochs(file_path:str, new_epoch:int) -> bool:
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        data['train']['epochs'] = new_epoch

    new_file_name = f'config_{new_epoch}.json'
    new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
    with open(new_file_path, 'w') as new_file:
        json.dump(data, new_file, indent=4)

    return new_file_path

def mindsflow_function(event, context) -> dict:
    # extract parameters from event
    file_path = 'train_configs/config.json'
    new_epoch = event.get("epochs")

    # modify the epochs in JSON file
    new_file_path = modify_epochs(file_path, new_epoch)

    url = upload_to_aws(new_file_path)

    os.remove(new_file_path)

    # formulate the result
    result = {
        'config_url': url
    }

    return result
