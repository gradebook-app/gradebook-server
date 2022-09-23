#!/bin/sh

echo REDIS_URL_ENV: $REDIS_URL_ENV

rqscheduler --url $REDIS_URL_ENV