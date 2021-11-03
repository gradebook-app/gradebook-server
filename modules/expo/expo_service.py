from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)

from requests.exceptions import ConnectionError, HTTPError

class ExpoService: 
    def __init__(self): 
        pass

    def send_push_notification(self, token, message, extra=None):
        try:
            response = PushClient().publish(
                PushMessage(to=token,
                            body=message,
                            data=extra))
        except PushServerError as exc:
            pass
        except (ConnectionError, HTTPError) as exc:
            pass
        try:
            response.validate_response()
        except DeviceNotRegisteredError:
           # remove token 
           pass
        except PushTicketError as exc:
            pass