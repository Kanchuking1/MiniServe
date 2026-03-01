# -- build flag is passed, build images
if [ "$1" == "--build" ]; then
    docker compose build inference
    docker compose build api
    docker compose build redis
    docker compose build worker
fi
docker compose up redis api worker