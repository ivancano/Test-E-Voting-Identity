import json
import boto3

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

def lambda_handler(event, context):
    result = False
    try:
        data = event
        result = compareFaces(data['face'], data['card_id'], data['bucket'])
        print("result")
        print(result)
    except Exception as e:
        print(e)
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
    
def compareFaces(sourceKey, targetKey, bucket):
    result = None
    try:
        response = rekognition.compare_faces(
            SourceImage={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': sourceKey,
                }
            },
            TargetImage={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': targetKey
                }
            }
        )
        if(len(response['FaceMatches'])):
            return True
        return False
    except rekognition.exceptions.InvalidParameterException as e:
        print("Error Rekognition Faces")
        print(e)
        return result
    except Exception as e:
        print(e)
        return result