"""Tool to pull intraday sleep data from Fitbit.

Register your app as a "personal app" with Fitbit Developers, online at
<https://dev.fitbit.com/apps/new>. Obtain a Client ID and Client Secret. Create
a separate file, secrets.py, that contains these two values. Go to the URL

https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=XXXXXX&scope=sleep

with XXXXXX replaced by your Client ID, then read the code off the end of the
URL to which you are redirected. Add this to secrets.py. That should look like:

    CLIENT_ID = ''
    CLIENT_SECRET = ''
    AUTH_CODE = ''

with only the three constants. You can then run this from the command line.

Usage:
    fitbit.py
    fitbit.py <start date>

Details:
    The start date should be written as yyyy-mm-dd (e.g., 2016-12-14). Note
    that if the start date was more than 150 days in the past, the script
    will terminate after 150 days of data, as 150/hour is the rate limit for
    the Fitbit API.
"""

import base64
import datetime
import json
import os
import requests
import sys

import secrets  # Python file with IDs and keys


def string_to_date(date_string):
    """Utility: convert date string YYYY-MM-DD to a date object."""

    d = datetime.datetime.strptime(date_string, '%Y-%m-%d')
    return d.date()


def get_date_list(start):
    """Create list of Dates between current date and provided start date

    params: 
        start: start date for the list, string formmated 'YYYY-MM-DD'
    return: 
        list of Date objects
    """

    end = datetime.date.today()
    start = string_to_date(start)
    delta = end - start

    d = [start + datetime.timedelta(days = i) for i in range(delta.days + 1)]

    return d


def get_token():
    """Obtains access token from Fitbit; returns response from server."""

    # Secrets stored in a separate file. 
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

    # Proper format for the code is b64-encoded; to do this, encode to
    # a bytestring then encode to b64, then decode it. 
    encoded_ID = base64.b64encode(FULL_ID.encode()).decode()
    header = {'Authorization': 'Basic ' + encoded_ID}
    
    req = requests.post(token_url, data = post_data, headers = header)

    if not req.json()['success']:
        print('Authentication failed')

    return req.json()


def pull_sleep_data(auth_token, start=None):
    """Extracts sleep data from Fitbit API and writes to text file.

    Submits requests to the Fitbit API for a sequence of days starting
    at a given day ('start'). The start date must be within 150 days of the
    current date, as the API limits users to 150 requests per hour. To obtain
    all sleep data, it is necessary to run several times with varying start
    dates.

    params:
        auth_token: from Fitbit for making requests; see get_token()
        start: start date to pull sleep data from, format 'yyyy-mm-dd'
    return: nothing
    """

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
        req_url = request_stem + str(date) + '.json'
        header = {'Authorization': token_type + ' ' + token}

        sleep_data = requests.post(req_url, headers = header).json()

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