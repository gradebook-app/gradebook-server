from pyfcm import FCMNotification
from twisted.internet import reactor
from config.config import config

class FCMService: 
    def __init__(self): 
        self.push_service = FCMNotification(api_key=config['fcm']['key'])
        reactor.run()

    def send_message(self, token, title, message): 
        self.push_service.notify_single_device(
            registration_id=token,
            message_title=title,
            message_body=message
        )
        