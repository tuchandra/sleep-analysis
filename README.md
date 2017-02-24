# sleep-analysis
A Python project to analyze my Fitbit sleep data.

## Overview
![Spring quarter sleep durations versus bedtimes](sample-image.png?raw=true)

This is a Python 3 project to obtain and analyze data on my sleep patterns, which has been collected nightly since July 2015 on my Fitbit Charge HR. The first part of the project is a script to access my nightly sleep logs; this script can be used by anyone hoping to access their data. The second part is the data analysis, in which I look into my spring sleep habits. This README focuses on the first part only.

Goals of this project included:
 * Learning to use Fitbit's API
 * Learning about the OAuth 2.0 protocol
 * Introducing myself to data analysis in Python
 * Gaining insight into my sleep patterns

Note: Fitbit is a registered trademark and service mark of Fitbit, Inc. My sleep analysis project is designed for personal use with the Fitbit platform. This product is not put out by Fitbit, and Fitbit does not service or warrant the functionality of this product.

## Part 1: Obtaining Minute-by-Minute Sleep Data
The first part of this project involves accessing my nightly, minute-by-minute sleep data from Fitbit's servers. Fitbit does not usually provide this through their smartphone or desktop apps; users can only generally see summary statistics. In order to access this data, I had to use Fitbit's API myself.

### Instructions
Clone the repo. Go to the [Fitbit Developers website](https://dev.fitbit.com/), register for an account, and register an app with them. The app will be for "Personal" use, which gives access to intraday sleep data. 

Create a file in a new directory, `credentials/client_secret.json`. (Note that this directory is listed in `.gitignore`.) This file should have:
```
{
  "web": {
    "client_id": "",
    "client_secret": "",
    "redirect_uris": [ "" ],
    "auth_uri": "https://api.fitbit.com/1/user/[client_id]/sleep/date",
    "token_uri": "https://api.fitbit.com/oauth2/token"
  }
}
```
Fill in the `client_id`, `client_secret`, and `redirect_uris` according to what you see on the Fitbit Developers console. Replace `[client_id]` with your client ID in `auth_uri`, and leave `token_uri` as is.

Finally, you are ready to run the app from the command line as `python fitbit.py <start date>`, with `<start date>` being optional, formatted as `yyyy-mm-dd`. This will write up to 150 days' worth of minute-by-minute sleep data to the directory `/logs/`.

### How Data Access Works
Accessing the data roughly follows this flow:
 * Try to read an access token from a file.
 * If no access token exists, generate a new one (this requires the user to authorize the script, which occurs in `get_token()`).
 * Try to read sleep data using this token. If the token has expired (this would happen if it was read from a file created some time ago), use the refresh token to generate and save a new one.
 * Read the sleep data with the new token.

The files are saved to a directory `logs` with names `yyyy-mm-dd.json`.

### Usage Notes
Fitbit limits API usage to 150 requests per hour. If you have more than 150 days of data, the script will write 150, then exit and tell you the start date for the top of the next hour.

If the start date is not entered, a default date of 150 days ago is chosen.

## Part 2: Data Analysis
Refer to `spring-sleep-analysis.ipynb` for the data analysis. This was done through a Jupyter notebook, making use of my spring quarter sleep data. Further detail is provided in that file; the image above is taken from the notebook.