from botocore.vendored import requests
import time
from datetime import datetime
import boto3
from urllib.parse import quote
import json
from boto3.dynamodb.conditions import Key,Attr
from decimal import Decimal


API_KEY = 'GkecMRt0c6K0GcseWeptJFprg-Dis_QUdA0IPVdjHhQzmYh7xdu8cuehEvf55jkOhkxPUeXyQW28n4_t4tMWjaeO5MxF5eCSZajNds6HFgZ8LTAHa6k554cXMlbmW3Yx'

API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'

OPEN_AT = time.time()
SEARCH_LIMIT = 3
from time import gmtime, strftime

def request(host, path, api_key, url_params=None):
    """Given your API_KEY, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))

    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }


    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()


def search(api_key, term, location, categories, sort_by):
    """Query the Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
        openAt (unix time epoch): The time at which a particular place will be open.
    Returns:
        dict: The JSON response from the request.
    """

    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        # 'open_at': openAt,
        'sort_by': sort_by,
        'categories':categories,
        'limit': SEARCH_LIMIT
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)


def query_api(term, location, categories, sort_by):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
        openAt (unix time epoch): The time at which a particular place will be open.
    """
    response = search(API_KEY, term, location, categories, sort_by)
    results = []

    businesses = response.get('businesses')

    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return


    else:
        for business in businesses:
            result = {
            "inserted_at" :  strftime("%Y-%m-%d %H:%M:%S", gmtime()),
            "id": business['id'],
            "price" :business['price'],
            "address" : business['location']['display_address'],
            "phone": business['phone'],
            "name": business['name'],
            "categories":business['categories'],
            "rating": business['rating'],
            "review_count" : business['review_count']
            }

            results.append(json.dumps(result))

    return results




def lambda_handler(event, context):
  print("hello cloudwatch!!")  
  sqs = boto3.resource('sqs')
  queue = sqs.get_queue_by_name(QueueName = 'test-messages')
  dynamodb = boto3.resource('dynamodb')
  table = dynamodb.Table('yelpChatbot')
  # Create an SNS client
  client = boto3.client("sns")

  resp = {
        "statusCode": 200,
        "body": "SNS Message sent!"
        }
  for message in queue.receive_messages():

    fall_back_message = message
    res_info = json.loads(message.body)
    cuisine = res_info['cuisine']
    term = "{} {}".format(res_info['cuisine'],res_info['city'])
    location = res_info['city']
    sort_by = "rating"
    categories = res_info['cuisine']
    phone_number = res_info['phone_number']
    date = res_info['date']
    time = res_info['time']
    number_of_people = res_info['num_people']
    
    complete_date = datetime.strptime(date + " " + time, '%Y-%m-%d %H:%M')
    
    recommendations  = query_api(term,location, categories, sort_by)
    
    print(recommendations)
    message = "Hello! So as per your request for {} restaurants in {} for {} people on {} at {}, here are my suggestions :\n".format(cuisine, location, number_of_people, date, time)
    counter = 0
  
    for recommendation in recommendations:
        counter +=1
        item = json.loads(recommendation, parse_float=Decimal)
        table.put_item(Item=item)
        address =  ' '.join(word for word in item['address'])
        message +="{}. {}, {}\n".format(counter,item['name'], address)
  
    # Publish a message to the client
    response = client.publish(
      PhoneNumber= phone_number,
      Message=message
      )

    if(response['ResponseMetadata']['HTTPStatusCode'] == 200):
            fall_back_message.delete()

  return resp