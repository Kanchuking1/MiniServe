# -- build flag is passed, build images
if [ "$1" == "--build" ]; then
    docker compose build inference
    docker compose build api
    docker compose build redis
    docker compose build worker
    docker compose up redis api worker
elif [ "$1" == "--scale" ]; then
    docker compose up redis api worker --scale worker=$2
else
    docker compose up redis api worker
fi
