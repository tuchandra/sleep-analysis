import secrets  # Python file with IDs and keys

import os, sys
import urllib.request, urllib.parse
import base64
import json
import datetime


# Instructions: Register your app with Fitbit Developers, and obtain a 
# client ID and client secret. Modify secrets.py to contain these two values.
# Next, go to the URL:
#
# https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=227VVG&scope=sleep
#
# and read the code off the URL to which you are redirected. Modify the
# constant AUTH_CODE in secrets.py. You are then able to run this file from
# the command line as "python fitbit.py <start date>" with <start date> being
# optional, formatted at yyyy-mm-dd.


def string_to_date(date_string):
    ''' Convert date string YYYY-MM-DD to a date object. '''

    d = datetime.datetime.strptime(date_string, '%Y-%m-%d')
    return d.date()


def get_date_list(start):
    ''' Create a list of all Dates between the current date and the provided
    start date.

    params: start = start date for the list, string formmated 'YYYY-MM-DD'
    return: list of date objects, []
    '''

    end = datetime.date.today()
    start = string_to_date(start)
    delta = end - start

    days_list = [start + datetime.timedelta(days = i) for i in range(delta.days + 1)]

    return days_list


def send_request(request):

    ''' Send a request and return a response. 

    params: request = Request object
    return: json response or None
    '''

    try:
        response = urllib.request.urlopen(request)
        response_json = json.loads(response.read().decode())

    except Exception as e:
        print('Error: Request failed')
        print(e.read())

    return response_json if response_json else None


def get_token():
    ''' Obtains an access token from Fitbit. 

    Returns response given by the server.
    '''

    # Secrets stored in a separate file. 
    # Refer to README.md for instructions on how to obtain these.
    CLIENT_ID = secrets.CLIENT_ID
    CLIENT_SECRET = secrets.CLIENT_SECRET
    AUTH_CODE = secrets.AUTH_CODE

    FULL_ID = CLIENT_ID + ':' + CLIENT_SECRET

    # Fitbit Token URL
    token_url = 'https://api.fitbit.com/oauth2/token'

    # Data for the POST request; refer to Fitbit developers website for standards
    # and requirements.
    post_data = {'code': AUTH_CODE, 
                 'grant_type': 'authorization_code', 
                 'client_id': CLIENT_ID, 
                 'redirect_uri': 'https://github.com/tuchandra/sleep-analysis'
                 }

    encoded_post_data = urllib.parse.urlencode(post_data).encode()

    # Create the request; proper format for the code is b64-encoded; to do
    # this, though, we have to encode the string to a bytestring first, 
    # then b64-encode it, then decode it to a regular string.
    req = urllib.request.Request(token_url, data = encoded_post_data)
    req.add_header('Authorization', 'Basic ' + base64.b64encode(FULL_ID.encode()).decode())

    # Send the request.
    auth_token = send_request(req)

    if not auth_token:
        print('Error: could not authenticate.')
        return

    return auth_token


def pull_sleep_data(auth_token, start=None):
    ''' Extracts sleep data from Fitbit API and writes to text file.

    Submits requests to the Fitbit API for a sequence of days starting
    at a given day ('start'). The start date must be within 150 days of the
    current date, as the API limits users to 150 requests per hour. To obtain
    all sleep data, it is necessary to run several times with varying start
    dates.

    params: auth_token = from Fitbit for making requests; see get_token()
            start = start date to pull sleep data from (yyyy-mm-dd)
    return: nothing    
    '''

    if not auth_token:
        print('Error: Authentication failed')
        return

    token = auth_token['access_token']
    refresh_token = auth_token['refresh_token']
    token_type = auth_token['token_type']
    user_id = auth_token['user_id']

    request_stem = 'https://api.fitbit.com/1/user/' + user_id + '/sleep/date/'

    # Choose default start date of 150 days ago
    if not start:
        start = str(datetime.date.today() - datetime.timedelta(days=150))
        print('Choosing default start date of 150 days ago, {0}'.format(start))

    dates = get_date_list(start)

    # Get directory to write all files to, and create if necessary
    script_path = os.path.abspath(__file__)
    script_dir = os.path.split(script_path)[0]
    write_dir = script_dir + '\\logs\\'

    if not os.path.exists(write_dir):
        os.makedirs(write_dir)

    # Fitbit API limits requests to 150 per hour, so 150 at a time
    for date in dates[:150]:
        # Format request and headers
        req = urllib.request.Request(request_stem + str(date) + '.json')
        req.add_header('Authorization', token_type + ' ' + token)

        sleep_data = send_request(req)

        if not sleep_data:
            print('Could not write sleep data for {0}.'.format(str(date)))
            return

        fpath = write_dir + str(date) + '.json'

        with open(fpath, 'a') as output:
            # Data needs to be formatted as proper JSON, which means replacing
            # ' with " and changing booleans to lowercase.
            formatted_data = str(sleep_data).replace("'", '"')
            formatted_data = formatted_data.replace('True', 'true')
            formatted_data = formatted_data.replace('False', 'false')
            
            output.write(formatted_data)

        print('Wrote sleep data to file /logs/{0}.json'.format(str(date)))

    # If there were more than 150 requests, notify user and provide the date
    # to start on next time. The only time the try statement will fail is if
    # there are fewer than 150 requests, in which case we are done.
    try:
        end_date = str(dates[150])
        print('Fitbit API rate limit reached.')
        print('Start from {0} at the next hour.'.format(end_date))

    except:
        print('Finished extracting data.')


if __name__ == "__main__":
    # See if a start date was provided
    try:
        start_date = sys.argv[1]

    except IndexError:
        start_date = None

    token = get_token()

    if not token:
        sys.exit(1)

    pull_sleep_data(token, start_date)