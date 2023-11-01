from dynamodb_adapter import DynamoDBAdapter
import os, json, base64
from uuid import uuid4
from datetime import datetime

TABLE_NAME = os.environ['tableName']
INDEX_NAME = os.environ['tableIndexName']
dynamodb_adapter = DynamoDBAdapter()


def build_query_params(type: str, start: str | None, limit: int | None): 
    params = {
        'attributeNames': {
            '#type': 'type',
        },
        'attributeValues': {
            ':type': {
                'S': type,
            }
        },
        'keyExpression': '#type = :type',
    }
    if start:
        params['start'] = decode_pagination_token(start)
    if limit:
        params['limit'] = limit
    return params

def decode_pagination_token(token: str | None) -> object | None:
    """"
    decode b64 string to json object
    """
    if token is None:
        return None
    base64_bytes = token.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('ascii')
    message_obj = json.loads(message)
    return message_obj

def encode_pagination_token(token: object | None) -> str | None:
    """"
    encode object to b64 string
    """
    if token is None:
        return None
    token_str = json.dumps(token)
    token_bytes = token_str.encode('ascii')
    base64_bytes = base64.b64encode(token_bytes)
    base64_message = base64_bytes.decode('ascii')
    return base64_message

def get_all(type: str, start: object = None, limit: int = None):
    query_params = build_query_params(type, start, limit)
    print(f'query params: {query_params}')

    response = dynamodb_adapter.query(
        table_name=TABLE_NAME,
        index_name=INDEX_NAME,
        **query_params,
    )
    
    data = {
        'count': response.get('Count', 0),
        'items': list(map(lambda x: dynamodb_adapter.unmarshall(x), response.get('Items', []))),
        'last': encode_pagination_token(response.get('LastEvaluatedKey'))
    }
    return data

def get_one(id: str) -> object | None:
    key = dynamodb_adapter.marshall({'id': id})
    print(f'fetching item with {key}')
    
    item_marshalled = dynamodb_adapter.get_item(TABLE_NAME, key)
    item = dynamodb_adapter.unmarshall(item_marshalled) if item_marshalled else None
    return item

def delete_one(id: str):
    key = dynamodb_adapter.marshall({'id': id})
    print(f'deleting item with {key}')
    
    dynamodb_adapter.delete_item(TABLE_NAME, key)

def create_item(item: dict) -> dict:
    now = datetime.now().isoformat()
    item = {
        'id': str(uuid4()), 
        'created': now, 
        'updated': now, 
        **item
    }
    print(f'Creating item {item}')
    
    dynamodb_adapter.put_item(table_name=TABLE_NAME, item=item)
    return item

def update_item(id: str, item: dict) -> dict:
    now = datetime.now().isoformat()
    key = {
        'id': id
    }
    item = { 
        **item,
        'updated': now, 
    }
    print(f'Updating item {item} key {key}')
    
    updated_item = dynamodb_adapter.update_item(table_name=TABLE_NAME, key=key, item=item)
    return updated_item