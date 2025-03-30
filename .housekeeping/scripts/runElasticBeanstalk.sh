#! /bin/bash
export VERSION="v3.0.0"
export ACCOUNTID="407495119696"
export FILE=".housekeeping/elasticbeanstalk/Dockerrun.aws.json"
export SECURITY_GROUP="sg-0be0e087a79a8b8b9"
source $1


/bin/cat <<EOM >$FILE
{
  "AWSEBDockerrunVersion": "1",
  "Image": {
    "Name": "$ACCOUNTID.dkr.ecr.us-east-1.amazonaws.com/django-webapp-docker-repo:$VERSION"
  },
  "Ports": [
    {
      "ContainerPort": 8000
    }
  ]
}
EOM

docker build -t django-docker:$VERSION .
docker tag django-docker:$VERSION $ACCOUNTID.dkr.ecr.us-east-1.amazonaws.com/django-webapp-docker-repo:$VERSION
aws ecr get-login-password | docker login --username AWS --password-stdin $ACCOUNTID.dkr.ecr.us-east-1.amazonaws.com
docker push  $ACCOUNTID.dkr.ecr.us-east-1.amazonaws.com/django-webapp-docker-repo:$VERSION
docker images
pushd .housekeeping/elasticbeanstalk
`python ../scripts/ebcreate.py ../../$1 $ELASTIC_BEANSTALK_ENV_NAME $SECURITY_GROUP`
popd
