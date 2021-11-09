from decouple import config

config = {
    "mongodb": {
        "uri": "mongodb://localhost:27017/gradebook-dev",
        "db": "gradebook-dev"
    },
    "jwt": {
        "token": "djedekdledkedk"
    },
    "fernet": {
        "key": "9V-3EF5gOsgm2bBJpdC8d1ucJ-01GNgKObLLgS-Guuc="
    },
    "fcm": {
        "key": config('FCM_TOKEN')
    }
}