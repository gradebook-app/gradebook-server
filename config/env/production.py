from decouple import config

config = {
    "mongodb": {
        "uri": "mongodb+srv://admin:Rq9hS8woGso0w5KD@gradebook.nwijt.mongodb.net/gradebook?authSource=admin&replicaSet=atlas-293qt9-shard-0&readPreference=primary&appname=MongoDB%20Compass&ssl=true",
        "db": "gradebook"
    },
     "jwt": {
        "token": config('JWT_TOKEN')
    },
    "fernet": {
        "key": config('FERNET_KEY')
    },
    "fcm": {
        "key": "AAAAa3is4iE:APA91bGQ0A6xAzV0lU__X-ILrCqGCZhJOsqew-4a0rRxPer6igq47EvYm-hsqdKurUwr08Ce8Kq0Dfi9HSpvpyZjvadZwSpoEkdoy5J7yalBzeyg2YLKeN0tAahvq-oYM0vhdLvX-qU7"
    }
}