from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import os

# Gera um par de chaves RSA
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=1024,
    backend=default_backend()
)
public_key = private_key.public_key()

# Gera uma chave simétrica AES
aes_key = os.urandom(32)

# Criptografa a chave AES com a chave pública RSA
cipher_rsa = public_key.encrypt(
    aes_key,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

# Descriptografa a chave AES com a chave privada RSA
decrypted_key = private_key.decrypt(
    cipher_rsa,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

print("Chave AES original:         ", aes_key)
print("Chave AES descriptografada: ", decrypted_key)
