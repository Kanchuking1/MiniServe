# -- build flag is passed, build images
if [ "$1" == "--build" ]; then
    docker compose build inference
    docker compose build api
    docker compose build redis
fi
docker compose up infernce
docker compose up redis api