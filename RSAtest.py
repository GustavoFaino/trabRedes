from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii

# Generate RSA keys (public and private)
keyPair = RSA.generate(1024)

pubKey = keyPair.publickey()
pubKeyPEM = pubKey.exportKey()

# Message to be encrypted
message = b'\xbcaU\x90\xc4|q\xf1\xbdi\xfb\x00\xa3\xee e\x8a\xb0\xb3\x11E\xf661\xc7a\x90\xbb\xcd|q\xd0'

# Encrypt the message
encryptor = PKCS1_OAEP.new(pubKey)
encrypted = encryptor.encrypt(message)

# Decrypt the message
decryptor = PKCS1_OAEP.new(keyPair)
decrypted = decryptor.decrypt(encrypted)

# Print the decrypted message
print('Decrypted:', decrypted)
