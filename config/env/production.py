from decouple import config

config = {
    "mongodb": {
        "uri": config('MONGO_URI'),
        "db": "gradebook"
    },
     "jwt": {
        "token": config('JWT_TOKEN')
    },
    "fernet": {
        "key": config('FERNET_KEY')
    },
    "fcm": {
        "key": config('FCM_TOKEN')
    }
}