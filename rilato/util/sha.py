from hashlib import sha1


def shasum(txt: str):
    return sha1(txt.encode()).hexdigest()
