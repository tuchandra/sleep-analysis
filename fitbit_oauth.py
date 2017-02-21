import base64
import json
import requests

def get_credentials():
    """Get Fitbit access token, according to OAuth2 flow.

    Obtains authorization code from provided client_secret information, then
    exchanges the code for an access token, which is returned.
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

    ### Obtain authorization code
    # User needs to go to a link in their browser and give us the callback URL;
    # might be possible to do this with some module in the future.
    auth_url = "https://www.fitbit.com/oauth2/authorize?response_type=code&client_id={0}&scope=sleep".format(client_id)
    print('Please go here and authorize access:\n\n{0}\n'.format(auth_url))
    auth_response = input('Enter the full redirected URL: ')
    
    # Format of callback URL is https:/.../whatever?code=auth_code#_=_
    # and we just want the code
    auth_code = auth_response.split("?")[-1]
    auth_code = auth_code[5:-4]

    ### Exchange auth_code for access token
    # Format request appropriately; see Fitbit docs for specifics
    data = "client_id={0}&code={1}&grant_type=authorization_code".format(client_id, auth_code)

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

    else:
        print("Error: could not authenticate")
        print (token.json())

    return token.json()


if __name__ == "__main__":
    c = get_credentials()
