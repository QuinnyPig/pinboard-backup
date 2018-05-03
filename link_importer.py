#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import os
import json
import boto3
import time
import sys
from boto3.dynamodb.conditions import Key, Attr

if os.getenv('INSIDE_LAMBDA') == "True":
    from base64 import b64decode
    ENCRYPTED_PINBOARD_TOKEN = os.getenv('PINBOARD_TOKEN')
    PINBOARD_TOKEN = boto3.client('kms').decrypt(
        CiphertextBlob=b64decode(ENCRYPTED_PINBOARD_TOKEN))['Plaintext']
else:
    PINBOARD_TOKEN = os.getenv('PINBOARD_TOKEN')
PINBOARD_API = 'https://api.pinboard.in/v1'

dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-west-2')
table = dynamodb.Table('lwia-links')


def get_approved_links(filter_tag):
    arguments = [
        'format=json',
        'tag=%s' % filter_tag,
        'auth_token=%s' % PINBOARD_TOKEN
    ]
    # If it's in Pinboard with the right tags, it's golden.
    url = PINBOARD_API + '/posts/all?' + '&'.join((arguments))
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        return r.json()
    else:
        sys.exit(1)


def get_issue():
    s3_bucket = 'lastweekinaws-utilities'
    key = 'issue.txt'
    s3 = boto3.resource('s3')
    obj = s3.Object(s3_bucket, key)
    return obj.get()['Body'].read().decode('utf-8')


def upload_link(link, issue):
    if not link['extended']:
        link['extended'] = "empty"

    sections = ['aws', 'community', 'tools', 'sponsor', 'tip']
    for x in sections:
        if x in link['tags']:
            section = x

    response = table.put_item(
        Item={
            'url': link['href'],
            'issue': issue,
            'timestamp': int(time.time()),
            'extended': link['extended'],
            'description': link['description'],
            section: '1'
        }
    )
    print(json.dumps(response, indent=4))


def prune_stale(issue):
    response = table.query(
        KeyConditionExpression=Key('issue').eq(issue),
        FilterExpression=Attr('timestamp').lt(int(time.time()) - 350)
    )
    for i in response['Items']:
        table.delete_item(
            Key={
                'issue': i['issue'],
                'url': i['url']
            }
        )


def lambda_handler(foo, bar):
    issue = int(get_issue())
    filter_tag = 'current'
    links = get_approved_links(filter_tag)
    for element in links:
        print("Attempting " + element['href'])
        upload_link(element, issue)
    print("Complete!")
    prune_stale(issue)
    return


# Keep this around to handle output / invocation properly outside of the
# Lambda environment.
if __name__ == "__main__":
    lambda_handler('foo', 'bar')
