import sys
from cryptography.fernet import Fernet
from decouple import config

if __name__ == "__main__": 
    try:
        encrypted_password = sys.argv[1]
        assert isinstance(encrypted_password, str)
        print("Key Provided")

        fernet_key = config("FERNET_KEY")
        assert isinstance(fernet_key, str)
        print("Fernet Key Provided")

        fernet = Fernet(fernet_key) 
        print("Fernet Initialized")
        print(encrypted_password)
        dycrypted_password = fernet.decrypt(encrypted_password.encode())

        print("Decrypted Password: ", dycrypted_password.decode())
    except: 
        print("No Encrypted Password Arg Provided or Invalid Format Provided")