import boto3
import functools 

class DynamoDBAdapter:
    def __init__(self, client=None, resource=None):
        self.client = client or boto3.client('dynamodb')
        self.resource = resource or boto3.resource('dynamodb')
        self._marshall = boto3.dynamodb.types.TypeSerializer()
        self._unmarshall = boto3.dynamodb.types.TypeDeserializer()

    def marshall(self, obj: dict):
        data = {k: self._marshall.serialize(v) for k, v in obj.items()}
        return data
    
    def unmarshall(self, obj: dict):
        data = {k: self._unmarshall.deserialize(v) for k, v in obj.items()}
        return data
    
    def get_item(self, table_name: str, key: dict) -> dict:
        response = self.client.get_item(
            TableName=table_name,
            Key=key
        )
        print(f'fetched item {response}')
        return response.get('Item')
    
    def delete_item(self, table_name: str, key: dict):
        response = self.client.delete_item(
            TableName=table_name,
            Key=key
        )
        print(f'deleted item {response}')
    
    def put_item(self, table_name: str, item: dict) -> dict:
        item_marshalled = self.marshall(item)

        self.client.put_item(
            TableName=table_name,
            Item=item_marshalled
        )
        return item_marshalled
    
    def update_item(self, table_name: str, key: dict, item: dict) -> dict | None:
        key_marshalled = self.marshall(key)
        
        def process_attribute_item(carry, item, total):
            key_value, i = item
            key, value = key_value
            carry['ExpressionAttributeNames'][f'#{key}'] = key
            carry['ExpressionAttributeValues'][f':{key}'] = self.marshall({key: value})[key]
            carry['UpdateExpression'] += f'#{key} = :{key}{", " if i < total-1 else ""}'
            return carry
        
        items = item.items()
        iterator = list(zip(items, [i for i in range(len(items))]))
        attributes = functools.reduce(lambda carry, x: process_attribute_item(carry, x, len(items)), iterator, {'ExpressionAttributeNames': {}, 'ExpressionAttributeValues': {}, 'UpdateExpression': 'SET '})
        
        args = {
            'TableName': table_name,
            'Key': key_marshalled,
            'ReturnValues': 'ALL_NEW',
            'ConditionExpression': f'attribute_exists({list(key.keys())[0]})',
            **attributes,
        }
        print(f'updating item {args}')

        response = self.client.update_item(**args)
        updated_item = response.get('Attributes')
        return self.unmarshall(updated_item) if updated_item else None

    def query(self, 
              table_name: str, 
              keyExpression: str, 
              attributeNames: object = None, 
              attributeValues: object = None, 
              filterExpression: str=None, 
              index_name: str = None, 
              limit: int = 100, 
              start: object = None
            ):
        args = {
            'TableName': table_name,
            'IndexName': index_name,
            'Select': 'ALL_ATTRIBUTES',
            'KeyConditionExpression': keyExpression,
            'ExpressionAttributeNames': attributeNames,
            'ExpressionAttributeValues': attributeValues
        }
        kwargs = {k: v for k,v in [['Limit', limit], ['ExclusiveStartKey', start], ['FilterExpression', filterExpression]] if v}
        
        response = self.client.query(**args, **kwargs)
        print(f'fetched data: {response}')
        return response
