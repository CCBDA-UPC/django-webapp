import base64
from github import Github, Auth
import sys
from dotenv import dotenv_values
import boto3
from git import Repo


trans = {
    'access_key': 'AWS_ACCESS_KEY_ID',
    'secret_key': 'AWS_SECRET_ACCESS_KEY',
    'token': 'AWS_SESSION_TOKEN'
}

otherSecrets = [
    'AWS_REGION',
    'ECR_REPOSITORY',
    'CONTAINER_NAME',
    'ELASTIC_BEANSTALK_APP_NAME',
    'ELASTIC_BEANSTALK_ENV_NAME',
]

try:
    CONFIGURATION_FILE = sys.argv[1]
except:
    print('ERROR: filename missing\npython updateGitHubSecrets.py filename')
    exit()

repo = Repo('../..')

github_repo = repo.config_reader().get('remote "origin"','url').replace('.git','').replace('https://github.com/','')

print(f'Updating secrets for repo "{github_repo}"')

config = dotenv_values(CONFIGURATION_FILE)

auth = Auth.Token(config['GITHUB_TOKEN'])
github_client = Github(auth=auth)

repo = github_client.get_repo(github_repo)

session = boto3.Session()
credentials = session.get_credentials().__dict__

for k, v in trans.items():
    print('\t', v)
    repo.create_secret(v, credentials[k], "actions")

sts = boto3.client("sts")
account_id = sts.get_caller_identity()["Account"]
repo.create_secret('AWS_ACCOUNT_ID', account_id, "actions")

for s in otherSecrets:
    print('\t', s)
    repo.create_secret(s, config[s], "actions")

# Update eb/Dockerrun.aws.json using Dockerrun.aws.json as template

print('\nUpdating Dockerrun.aws.json')

with open('../Dockerrun.aws.json', 'r') as f:
    s = f.read()

dockerrun = {
    'ECR_REPOSITORY': config['ECR_REPOSITORY'],
    'AWS_ACCOUNT_ID': account_id
}

dockerrun_content = s % dockerrun

try:
    contents = repo.get_contents("eb/Dockerrun.aws.json")
    f = base64.b64decode(contents.content).decode('utf8')
    if f != dockerrun_content:
        repo.update_file(contents.path, "updated Dockerrun.aws.json", dockerrun_content, contents.sha, branch='main')
except Exception as e:
    repo.create_file('eb/Dockerrun.aws.json', 'added Dockerrun.aws.json', dockerrun_content, branch='main')

with open('../elasticbeanstalk/Dockerrun.aws.json', 'w') as f:
    f.write(dockerrun_content)
