from config.env.development import config as devConfig
from config.env.production import config as prodConfig
from decouple import config, UndefinedValueError

try: 
    node_env = config("NODE_ENV")
except UndefinedValueError: 
    node_env = "development"

config = prodConfig if node_env == "production" else devConfig
