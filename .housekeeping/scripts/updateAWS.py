from dotenv import dotenv_values
import boto3
import sys

trans = {
    'access_key': 'AWS_ACCESS_KEY_ID',
    'secret_key': 'AWS_SECRET_ACCESS_KEY',
    'token': 'AWS_SESSION_TOKEN'
}

try:
    CONFIGURATION_FILE = sys.argv[1]
except:
    print('ERROR: filename missing\npython updateAWS.py filename')
    exit()

config = dotenv_values(CONFIGURATION_FILE)

session = boto3.Session()
credentials = session.get_credentials().__dict__

changed = False
for k, v in trans.items():
    if config[v] != credentials[k]:
        config[v] = credentials[k]
        changed = True

if changed:
    print ('AWS credentials have changed')
    newfile = ''
    for k, v in config.items():
        newfile += f'{k}={v}\n'
    with open(CONFIGURATION_FILE, 'w') as fw:
        fw.write(newfile)