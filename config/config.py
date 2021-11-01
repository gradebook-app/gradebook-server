from config.env.development import config as devConfig
from config.env.production import config as prodConfig
from decouple import config, UndefinedValueError

try: 
    env_mode = config("ENV_MODE")
except UndefinedValueError: 
    env_mode = "development"

config = prodConfig if env_mode == "production" else devConfig
