#!/usr/bin/env bash -x -v

mktemp -d ./tempDir

LOCAL_PATH=$(cd ./tempDir; pwd)
LEADER_PATH=/test/data
UUID=$(python -c 'import uuid; print uuid.uuid4()')
LEADER_IP=172.17.0.2
LEADER_PORT=5050
LEADER=toil-leader-$UUID
WORKER=toil-worker-$UUID

echo Starting containers
docker run -d -v $LOCAL_PATH:$LEADER_PATH \
            --name $LEADER quay.io/ucsc_cgl/toil-leader \
            --ip=$LEADER_IP \
            --registry=in_memory

docker run -d --volumes-from $LEADER \
                --name $WORKER quay.io/ucsc_cgl/toil-worker \
                --master=$LEADER_IP:$LEADER_PORT \
                --work_dir=/tmp/

echo Copying script into leader
docker cp ./test/testToil.py $LEADER:/home/

echo Running script
docker exec $LEADER /usr/bin/python /home/testToil.py \
                                    $LEADER_PATH/jobStore \
                                    --batchSystem=mesos \
                                    --mesosMaster=$LEADER_IP:$LEADER_PORT \
                                    --clean=always

EXITCODE=$?

echo Stopping containers
docker stop $LEADER
docker stop $WORKER
rm -r ./tempDir

if [[ $EXITCODE -ne 0 ]] ; then
    echo 'Test failed'
    exit 1
fi

echo Test succeeded
