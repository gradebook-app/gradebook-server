from decouple import config

config = {
    "mongodb": {
        "uri": "mongodb+srv://admin:Rq9hS8woGso0w5KD@gradebook.nwijt.mongodb.net/gradebook?authSource=admin&replicaSet=atlas-293qt9-shard-0&readPreference=primary&appname=MongoDB%20Compass&ssl=true"
    },
     "jwt": {
        "token": config('JWT_TOKEN')
    },
    "fernet": {
        "key": config('FERNET_KEY')
    }
}