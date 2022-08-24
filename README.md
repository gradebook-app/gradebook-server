# About 

API that powers Gradebook / Genesus App

# Start Virtual Environment

- . ./env/bin/activate (MacOS)

# Install Python Dependencies

- pip install -r requirements.txt

# Install Ruby Dependencies

- bundle install 

# Run Locally

Run These Commands to start server locally. 
Important Note: Run MongoDB Service commands first.

1. redis-server
2. rqscheduler
3. export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES (Run this only if on MacOS)
4. rq worker
5. python app.py

# Run MongoDB Service Locally: 

1. docker-compose up

# Scale Worker Count on Heroku

heroku scale worker=10 -a gradebook-web-api