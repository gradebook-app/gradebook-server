# About 

API that powers Gradebook / Genesus App

# Run Locally

Run These Commands to start server locally 

1. redis-server
2. rqscheduler
3. export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES (Run this only if on OSX)
4. rq worker
5. python app.py


# Scale Worker Count on Heroku

heroku scale worker=10 -a gradebook-web-api