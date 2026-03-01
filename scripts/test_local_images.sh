'''
To curl all the images in the data folder
sudo apt-get install -y jq
'''


for image in ./data/*.png; do
    echo "Testing $image"
    response=$(curl -X POST http://localhost:8000/submit -F "file=@$image")
    echo "Response: $response"
    # Reponse format is {"job_id": "1234567890"}
    job_id=$(echo $response | jq -r '.job_id')
    echo "Job ID: $job_id"
    echo "Waiting for result..."
    while true; do
        response=$(curl -X GET http://localhost:8000/result/$job_id)
        status=$(echo $response | jq -r '.status')
        if [ "$status" == "completed" ]; then
            break
        fi
        sleep 1
    done
    echo "Result: $response"
    echo "--------------------------------"
done