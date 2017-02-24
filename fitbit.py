"""Tool to pull intraday sleep data from Fitbit.

Register your app as a "personal app" with Fitbit Developers, online at
<https://dev.fitbit.com/apps/new>. Fill out client_secret.json according
to the guidelines in the README. You are then ready to pull your sleep data.

Usage:
    fitbit.py
    fitbit.py <start date>

Details:
    The start date should be written as yyyy-mm-dd (e.g., 2016-12-14). Note
    that if the start date was more than 150 days in the past, the script
    will terminate after 150 days of data, as 150/hour is the rate limit for
    the Fitbit API. If the start date is not specified, it will choose a
    date 150 days in the past.
"""


import base64
import datetime
import json
import os
import requests
import sys


def string_to_date(date_string):
    """Utility: convert date string YYYY-MM-DD to a date object."""

    d = datetime.datetime.strptime(date_string, '%Y-%m-%d')
    return d.date()


def get_date_list(start):
    """Create list of date objects between current and provided start date.

    params: 
        start: start date for the list, string formmated 'YYYY-MM-DD'
    return: 
        list of date objects
    """

    end = datetime.date.today()
    start = string_to_date(start)
    delta = end - start

    d = [start + datetime.timedelta(days = i) for i in range(delta.days + 1)]

    return d


def get_access_token(refresh_token = None):
    """Get Fitbit access token according to OAuth2 flow.

    Use client_secret file to obtain an authorization code, then exchange the
    code for an access token, per OAuth2 specification.

    If refresh_token is specified, this uses it to obtain a new access token
    without the user having to reauthenticate.

    params: 
        refresh_token - if specified, generates a new access token using this
    return:
        access_token - JSON object
    """

    ### Find and read client_secret
    # Format of file:
    # { "web" : { "auth_uri" : "...",
    #             "token_uri" : "...",
    #             "redirect_uris" : [ ... ],
    #             "client_id" : "...",
    #             "client_secret" : "...",
    #            }
    #  }
    #

    secret_file = "credentials/client_secret.json"

    with open(secret_file) as f:
        secret_contents = json.loads(f.read())
        secret_contents = secret_contents['web']

    # Unpack contents
    client_id = secret_contents['client_id']
    client_secret = secret_contents['client_secret']
    redirect_uri = secret_contents['redirect_uris'][0]
    auth_uri = secret_contents['auth_uri']  # Not used
    token_uri = secret_contents['token_uri']

    # If refresh token specified, we don't need to reauthenticate; just set up
    # the request to refresh our access token
    if refresh_token:
        data = "grant_type=refresh_token&refresh_token={0}".format(refresh_token)

    # Otherwise, generate new auth code and access token
    else:
        # User needs to go to a link in their browser and give us the callback URL;
        # might be possible to do this with some module in the future.
        auth_url = "https://www.fitbit.com/oauth2/authorize?response_type=code&client_id={0}&scope=sleep".format(client_id)
        print('Please go here and authorize access:\n\n{0}\n'.format(auth_url))
        auth_response = input('Enter the full redirected URL: ')
        
        # Format of callback URL is https:/.../whatever?code=auth_code#_=_
        # and we just want the code
        auth_code = auth_response.split("?")[-1]
        auth_code = auth_code[5:-4]

        # Exchange auth_code for access token
        data = "client_id={0}&code={1}&grant_type=authorization_code".format(client_id, auth_code)

    # Generate headers; see Fitbit docs for specifications
    full_id = client_id + ":" + client_secret
    encoded_ID = base64.b64encode(full_id.encode()).decode().strip()
    headers = {'Authorization': 'Basic ' + encoded_ID,
               'Content-Type': 'application/x-www-form-urlencoded'}

    token = requests.post(token_uri, data = data, headers = headers)

    # Write token to file
    if token.status_code == 200:
        print("Successfully authenticated and obtained access token.")

        with open("credentials/fitbit_token.json", "w") as f:
            json.dump(token.json(), f)

        print("Saved new access token to file.")

    else:  # failed
        print (token.json())
        return None

    return token.json()


def pull_sleep_data(token, start=None):
    """Extracts sleep data from Fitbit API and writes to JSON files.

    Submits requests to the Fitbit API for a sequence of days starting
    at a given day ('start'). The start date must be within 150 days of the
    current date, as the API limits users to 150 requests per hour. To obtain
    all sleep data, it is necessary to run several times with varying start
    dates.

    params:
        token: from Fitbit for making requests; see get_token()
        start: start date to pull sleep data from, format 'yyyy-mm-dd'
    return: 
        401 if access token was expired, else None
    """

    access_token = token['access_token']
    refresh_token = token['refresh_token']  # not used
    token_type = token['token_type']
    user_id = token['user_id']

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
        header = {'Authorization': token_type + ' ' + access_token}

        sleep_data = requests.post(req_url, headers = header)

        if sleep_data.status_code == 401:
            print("Access token expired.")
            return 401

        fpath = write_dir + str(date) + '.json'

        with open(fpath, 'a') as output:
            # Data needs to be formatted as proper JSON, which means replacing
            # ' with " and changing booleans to lowercase.
            formatted_data = str(sleep_data.json()).replace("'", '"')
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

    # Try to read token from file; otherwise, get new token
    try:
        with open("credentials/fitbit_token.json") as f:
            token = json.load(f)
            print("Successfully read access token from file.")

    except:
        print("Access token not found; generating new one.")
        token = get_access_token()

    # If token still doesn't exist, then we can't do anything else
    if not token:
        print("Unable to generate access token; exiting.")
        sys.exit(1)

    # Try to get data; if we have a return value, we need a new token
    error = pull_sleep_data(token, start_date)

    if error == 401:
        # Refresh token, then try again
        print("Refreshing access token.")
        refresh_token = token["refresh_token"]
        token = get_access_token(refresh_token = refresh_token)

        pull_sleep_data(token, start_date)