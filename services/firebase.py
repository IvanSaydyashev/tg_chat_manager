import firebase_admin
from cryptography.hazmat.primitives.keywrap import aes_key_wrap
from firebase_admin import credentials, db

class FirebaseClient:
    def __init__(self, firebase_url: str, secret: str) -> None:
        """
        firebase_url: Firebase Runtime DB URL.
        secret: Firebase Runtime DB secret.
        """
        self.url = firebase_url
        self.secret = secret

        if not firebase_admin._apps:
            cred = credentials.Certificate(secret)
            firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})
        self.db = db

    async def write(self, path: str, data: int|dict|str|object) -> None:
        self.db.reference(path).set(data)


    async def update(self, path: str, data: dict) -> None:
        self.db.reference(path).update(data)


    async def read(self, path: str) -> object|str|int|dict|None:
        return self.db.reference(path).get()


    async def delete(self, path: str) -> None:
        self.db.reference(path).delete()