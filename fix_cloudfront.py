import os
import sys
import time
import boto3
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / 'backend' / '.env')

REGION = 'us-east-1'
cf = boto3.client('cloudfront', region_name=REGION)
DIST_ID = 'E26WL7E30B02YC'

print(f"Fetching config for CloudFront distribution {DIST_ID}...")
res = cf.get_distribution_config(Id=DIST_ID)
etag = res['ETag']
config = res['DistributionConfig']

api_origin_id = None
for orig in config['Origins']['Items']:
    if orig['Id'].startswith('API-'):
        api_origin_id = orig['Id']
        break

if not api_origin_id:
    raise RuntimeError("API origin not found in distribution")

config['CacheBehaviors'] = {
    'Quantity': 1,
    'Items': [
        {
            'PathPattern': '/api/*',
            'TargetOriginId': api_origin_id,
            'TrustedSigners': {
                'Enabled': False,
                'Quantity': 0
            },
            'TrustedKeyGroups': {
                'Enabled': False,
                'Quantity': 0
            },
            'ViewerProtocolPolicy': 'redirect-to-https',
            'AllowedMethods': {
                'Quantity': 7,
                'Items': ['HEAD', 'DELETE', 'POST', 'GET', 'OPTIONS', 'PUT', 'PATCH'],
                'CachedMethods': {'Quantity': 2, 'Items': ['HEAD', 'GET']},
            },
            'SmoothStreaming': False,
            'Compress': True,
            'LambdaFunctionAssociations': {'Quantity': 0},
            'FunctionAssociations': {'Quantity': 0},
            'FieldLevelEncryptionId': '',
            'CachePolicyId': '4135ea2d-6df8-44a3-9df3-4b5a84be39ad',
            'OriginRequestPolicyId': 'b689b0a8-53d0-40ab-baf2-68738e2966ac',
            'GrpcConfig': {'Enabled': False}
        }
    ]
}

# Remove 404 from CustomErrorResponses, keep only 403
config['CustomErrorResponses'] = {
    'Quantity': 1,
    'Items': [
        {
            'ErrorCode': 403,
            'ResponsePagePath': '/index.html',
            'ResponseCode': '200',
            'ErrorCachingMinTTL': 0,
        }
    ]
}

print(f"Updating CloudFront distribution {DIST_ID}...")
update_res = cf.update_distribution(
    Id=DIST_ID,
    IfMatch=etag,
    DistributionConfig=config
)
print("CloudFront distribution updated successfully!")

print("Triggering cache invalidation...")
cf.create_invalidation(
    DistributionId=DIST_ID,
    InvalidationBatch={
        'Paths': {'Quantity': 1, 'Items': ['/*']},
        'CallerReference': str(time.time()),
    }
)
print("Invalidation triggered successfully!")
