import json
import service
from botocore import exceptions

def return_response(status_code: int, body=None):
    return {
        "headers": {
            "Content-Type": "application/json"
        },
        "statusCode": status_code,
        "body": json.dumps(body, default=str) if body else None,
    }

def handler_get_all(event, _context):
    print(f'event {event}')
    params = event.get('queryStringParameters', {}) or {}

    start_param, limit_param, type_param = params.get('start'), params.get('limit'), params.get('type')
    if not type_param:
        return return_response(status_code=400, body={'error': 'Missing required "type" param'})
    
    data = service.get_all(type_param, start_param, int(limit_param) if limit_param else None)
    return return_response(status_code=200, body=data)


def handler_get_one(event, _context):
    print(f'event {event}')
    params = event.get('pathParameters', {}) or {}

    id = params.get('id')
    item = service.get_one(id)
    if item is None:
        return return_response(status_code=404, body=None)
    return return_response(status_code=200, body=item)


def handler_delete_one(event, _context):
    print(f'event {event}')
    params = event.get('pathParameters', {}) or {}

    id = params.get('id')
    service.delete_one(id)
    return return_response(status_code=204, body=None)

def handler_create(event, _context):
    print(f'event {event}')
    try:
        body = json.loads(event['body'])

        if body.get('type') is None:
            raise Exception('Missing type property')
    except Exception as error:
        print(f'Error: {error}')
        return return_response(status_code=400, body={'error': 'Invalid input'})
    
    item = service.create_item(body)
    
    return return_response(status_code=201, body=item)

def handler_update(event, _context):
    print(f'event {event}')
    params = event.get('pathParameters', {}) or {}

    try:
        body = json.loads(event['body'])
        if not bool(body):
            raise Exception('Input cannot be empty')
    except Exception as error:
        print(f'Error: {error}')
        return return_response(status_code=400, body={'error': 'Invalid input'})
    
    id = params.get('id')
    try:
        item = service.update_item(id, body)
        return return_response(status_code=200, body=item)
    except exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return return_response(status_code=404, body=None)
        raise error
    except Exception as error:
        print(f'Error: {error}')
        return return_response(status_code=500, body={'error': 'Internal server error'})