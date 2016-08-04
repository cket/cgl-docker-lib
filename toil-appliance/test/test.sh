#!/usr/bin/env bash

echo 'starting containers'
docker run -d -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY quay.io/ucsc_cgl/toil-leader
docker run -d quay.io/ucsc_cgl/toil-worker --master=172.17.0.2:5050 --work_dir=/tmp/

LEADER=$(docker ps | grep toil-leader | awk '{print $1;}')
WORKER=$(docker ps | grep toil-worker | awk '{print $1;}')

echo 'copying script into leader'
docker cp ./test/testToil.py $LEADER:/home/

UUID=$(python -c 'import uuid; print uuid.uuid4()')

echo 'running script'
docker exec $LEADER /usr/bin/python /home/testToil.py aws:us-west-2:toil-appliance$UUID \
--batchSystem=mesos --mesosMaster=172.17.0.2:5050 -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
-e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY --clean=always

EXITCODE=$?

echo 'stopping containers'
docker stop $LEADER
docker stop $WORKER

if [[ $EXITCODE -ne 0 ]] ; then
    echo 'test failed'
    exit 1
fi

echo 'test succeeded'
