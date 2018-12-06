"""
 This code sample demonstrates an implementation of the Lex Code Hook Interface
 in order to serve a bot which manages dentist appointments.
 Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
 as part of the 'MakeAppointment' template.

 For instructions on how to set up and test this bot, as well as additional samples,
 visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""

import json
import dateutil.parser
import datetime
import time
import os
import math
import random
import logging
import boto3


logger = logging.getLogger()
logger.setLevel(logging.ERROR)
sqs = boto3.resource('sqs')


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message, response_card):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message,
            'responseCard': response_card
        }
    }

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

def validate_cuisine(cuisine_type):
    cuisine_types = ['chinese','thai','asian','indian','american','japanese']
    if(cuisine_type):
        return cuisine_type.lower() in cuisine_types

def validate_city(city):
    US_cities = ['new york', 'los angeles', 'chicago', 'houston', 'philadelphia', 'phoenix', 'san antonio',
                    'san diego', 'dallas', 'san jose', 'austin', 'jacksonville', 'san francisco', 'indianapolis',
                    'columbus', 'fort worth', 'charlotte', 'detroit', 'el paso', 'seattle', 'denver', 'washington dc',
                    'memphis', 'boston', 'nashville', 'baltimore', 'portland','brooklyn', 'bronx', 'manhattan', 'queens','staten island',
                    'long island city']
                    
    if(city):
        return city.lower() in US_cities

def validate_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except:
        return False

def validate_contact(contact):
    contact = str(contact)
    contact = str.replace(contact,'-','')
    contact = str.replace(contact,'(','')
    contact = str.replace(contact,')','')
    contact = str.replace(contact,' ','')
    
    if (len(contact)!=11):
        return False
    elif (len(contact) == 11):
        if(contact[0] == '1'):
            return True
        else:
            return False
    
    
def validate_userDetails(cuisine_type,city,date,contact,time):
    cuisine_types = ['chinese','thai','asian','indian','american','japanese']
                    
    if(cuisine_type != None and validate_cuisine(cuisine_type) != True):
        return build_validation_result(False,'cuisine','We do not provide support for {} cuisine yet. Would you like to try some different cuisine from {}?'.format(cuisine_type,','.join(cuisine_types)))

    if(city != None and validate_city(city) != True):
        return build_validation_result(False,'cityName','We do not provide support in {} yet. Please select another location.'.format(city))
        
    if(contact != None and validate_contact(contact) != True):
        return build_validation_result(False,'PhoneNumber','Please enter a valid Contact Number')
        
    if date != None:
        if(validate_date(date) != True):
            return build_validation_result(False,'RDate','I cannot understand the date. For which date would you like to book a reservation?')
        elif(datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today()):
            return build_validation_result(False,'RDate','You cannot make reservation for a previous date. Please enter a valid date.')
    
    # if time!= None:
    #     dateTime = date + " " + time
    #     print (dateTime)
    #     if(datetime.datetime.strptime(dateTime, '%Y-%m-%d %H:%M') > datetime.datetime.today()):
    #         print ("inside the time block")
    #         return build_validation_result(False,'RTime','You cannot make reservation for a previous time. Please enter a valid time.')
    
    print (cuisine_type,city,date,contact,time)
    return build_validation_result(True,None,None)



def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def make_appointment(intent_request):
    res_info = {
        "city" : intent_request['currentIntent']['slots']['cityName'],
        "date" : intent_request['currentIntent']['slots']['RDate'],
        "time" : intent_request['currentIntent']['slots']['RTime'],
        "num_people" : intent_request['currentIntent']['slots']['PeopleCount'],
        "cuisine" : intent_request['currentIntent']['slots']['cuisine'],
        "phone_number" : intent_request['currentIntent']['slots']['PhoneNumber']
        }
        
    source = intent_request['invocationSource']
    print(source)
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    slots = intent_request['currentIntent']['slots']
    
    if intent_request['invocationSource'] == 'DialogCodeHook':
        print("inside dialog code hook")
        result = validate_userDetails(res_info['cuisine'], res_info['city'], res_info['date'], res_info['phone_number'],res_info['time'])
        print("validation result:",result)
        print(type(result))
        if result['isValid'] != True:
            slots[result['violatedSlot']] = None
            response = {
                    'sessionAttributes' : intent_request['sessionAttributes'],
                    'dialogAction': {
                            'type' : 'ElicitSlot',
                            'intentName' : intent_request['currentIntent']['name'],
                            'slots' : slots,
                            'slotToElicit' : result['violatedSlot'],
                            'message' : result['message']
                    }
            }
            print("Invalid response:",response)
            return response
            
        print("after invalid return 1")
        
        response = {
                'sessionAttributes' : intent_request['sessionAttributes'],
                'dialogAction' : {
                        'type' : 'Delegate',
                        'slots' : slots
                }
        }
        print("valid response:",response)
        return response
    
    # Book the appointment.  In a real bot, this would likely involve a call to a backend service.
    queue = sqs.get_queue_by_name(QueueName='test-messages')
    response = queue.send_message(MessageBody=json.dumps(res_info))
    print(response)

    return close(
        output_session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': "Alright! I'll send your suggestions shortly!"
        }
    )



""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'Thankyou':
        return make_appointment(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    print(event)
    print(context)
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
