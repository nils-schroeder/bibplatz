import boto3
import os

AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY"]
AWS_SECRET_KEY = os.environ["AWS_SECRET_KEY"]


def get_all_users():
    dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY,
                              region_name='eu-central-1')
    table = dynamodb.Table('bibbot_user')

    response = table.scan()
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return data


def create_user(chat_id):
    dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY,
                              region_name='eu-central-1')
    table = dynamodb.Table('bibbot_user')

    response = table.put_item(
        Item={
            "chat_id": str(chat_id),
            "credentials": {
                "readernumber": "",
                "password": ""
            },
            "preferences": {"institution": "",
                            "area": "",
                            "fitting": [],
                            "from_time": "",
                            "to_time": ""
                            },
            "enabled": False
        }
    )

    return response


def update_credentials(chat_id, credentials):
    dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY,
                              region_name='eu-central-1')
    table = dynamodb.Table('bibbot_user')
    response = table.update_item(
        Key={
            'chat_id': str(chat_id)
        },
        UpdateExpression="set credentials=:c",
        ExpressionAttributeValues={
            ":c": credentials
        }
    )
    return response


def update_preferences(chat_id, preferences):
    dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY,
                              region_name='eu-central-1')
    table = dynamodb.Table('bibbot_user')
    response = table.update_item(
        Key={
            'chat_id': str(chat_id)
        },
        UpdateExpression="set preferences=:p",
        ExpressionAttributeValues={
            ":p": preferences
        }
    )
    return response


def update_active(chat_id, value):
    dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY,
                              region_name='eu-central-1')
    table = dynamodb.Table('bibbot_user')
    response = table.update_item(
        Key={
            'chat_id': str(chat_id)
        },
        UpdateExpression="set enabled=:e",
        ExpressionAttributeValues={
            ":e": value
        }
    )
    return response


def get_data(chat_id):
    dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY,
                              region_name='eu-central-1')
    table = dynamodb.Table('bibbot_user')

    try:
        response = table.get_item(Key={'chat_id': str(chat_id)})
    except Exception:
        pass
    else:
        item = response["Item"]
        creds = item["credentials"]
        prefs = item["preferences"]

        fittings = ",".join(prefs['fitting'])

        format_string = f"Karten-ID: {creds['readernumber']}\nPasswort: {creds['password']}\n" \
                        f"Standort: {prefs['institution']}\nArea: {prefs['area']}\nAuswahl: {fittings}\n" \
                        f"Beginn: {prefs['from_time']} Uhr\nEnde: {prefs['to_time']} Uhr\nAktiviert: {item['enabled']}"

        return format_string
