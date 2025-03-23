from github import Github, Auth, Secret
import sys
from dotenv import dotenv_values
import boto3

trans = {
    'access_key': 'AWS_ACCESS_KEY_ID',
    'secret_key': 'AWS_SECRET_ACCESS_KEY',
    'token': 'AWS_SESSION_TOKEN'
}

try:
    CONFIGURATION_FILE = sys.argv[1]
    REPO = sys.argv[2]
except:
    print('ERROR: filename missing\npython updateGitHubSecrets.py filename repo')
    exit()

config = dotenv_values(CONFIGURATION_FILE)

auth = Auth.Token(config['GITHUB_TOKEN'])
github_client = Github(auth=auth)

repo = github_client.get_repo(f"CCBDA-UPC/{REPO}")

session = boto3.Session()
credentials = session.get_credentials().__dict__

for k, v in trans.items():
    repo.create_secret(v,credentials[k], "actions")

sts = boto3.client("sts")
account_id = sts.get_caller_identity()["Account"]
repo.create_secret('AWS_ACCOUNT_ID',account_id, "actions")
