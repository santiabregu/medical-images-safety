"""
Módulo de cifrado híbrido para imágenes médicas.
Usa AES-128 para cifrar las imágenes y RSA-1024 para cifrar la clave AES.
"""

import os
import numpy as np
from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# PyCryptodome para OCB (cryptography no soporta OCB)
try:
    from Crypto.Cipher import AES as CryptoAES
    from Crypto.Random import get_random_bytes
    PYCRYPTODOME_AVAILABLE = True
except ImportError:
    PYCRYPTODOME_AVAILABLE = False


def generate_rsa_keypair():
    """
    Genera un par de claves RSA-1024 (pública y privada).
    
    Returns:
        tuple: (private_key, public_key)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


def save_rsa_keys(private_key, public_key, private_key_path="keys/private_key.pem", 
                  public_key_path="keys/public_key.pem"):
    """
    Guarda las claves RSA en archivos PEM.
    
    Args:
        private_key: Clave privada RSA
        public_key: Clave pública RSA
        private_key_path: Ruta donde guardar la clave privada
        public_key_path: Ruta donde guardar la clave pública
    """
    os.makedirs(os.path.dirname(private_key_path), exist_ok=True)
    
    # Guardar clave privada
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(private_key_path, 'wb') as f:
        f.write(private_pem)
    
    # Guardar clave pública
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(public_key_path, 'wb') as f:
        f.write(public_pem)


def load_rsa_private_key(key_path="keys/private_key.pem"):
    """
    Carga una clave privada RSA desde un archivo PEM.
    
    Args:
        key_path: Ruta al archivo de clave privada
        
    Returns:
        Clave privada RSA
    """
    with open(key_path, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    return private_key


def load_rsa_public_key(key_path="keys/public_key.pem"):
    """
    Carga una clave pública RSA desde un archivo PEM.
    
    Args:
        key_path: Ruta al archivo de clave pública
        
    Returns:
        Clave pública RSA
    """
    with open(key_path, 'rb') as f:
        public_key = serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )
    return public_key


def generate_aes_key():
    """
    Genera una clave AES-128 (16 bytes).
    
    Returns:
        bytes: Clave AES de 16 bytes
    """
    return os.urandom(16)


def encrypt_image_hybrid(image_path, public_key_path, output_path):
    """
    Cifra una imagen usando cifrado híbrido (AES-128 + RSA-1024).
    
    Flujo:
    1. Genera una clave AES-128 aleatoria
    2. Cifra la imagen con AES-128 en modo CBC
    3. Cifra la clave AES con RSA-1024 usando la clave pública
    4. Guarda la imagen cifrada y la clave AES cifrada
    
    Args:
        image_path: Ruta a la imagen a cifrar
        public_key_path: Ruta a la clave pública RSA
        output_path: Ruta donde guardar la imagen cifrada
        
    Returns:
        str: Ruta al archivo que contiene la clave AES cifrada
    """
    # Cargar imagen y convertir a bytes
    img = Image.open(image_path)
    width, height = img.size
    img_array = np.array(img)
    img_bytes = img_array.tobytes()
    
    # Generar clave AES-128
    aes_key = generate_aes_key()
    
    # Generar IV (Initialization Vector) para CBC
    iv = os.urandom(16)
    
    # Cifrar imagen con AES-128-CBC
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(img_bytes)
    padded_data += padder.finalize()
    
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_image = encryptor.update(padded_data) + encryptor.finalize()
    
    # Cifrar la clave AES con RSA-1024
    public_key = load_rsa_public_key(public_key_path)
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Guardar imagen cifrada (dimensiones + IV + datos cifrados)
    # Formato: 4 bytes width + 4 bytes height + 16 bytes IV + datos cifrados
    width_bytes = width.to_bytes(4, byteorder='big')
    height_bytes = height.to_bytes(4, byteorder='big')
    encrypted_data = width_bytes + height_bytes + iv + encrypted_image
    with open(output_path, 'wb') as f:
        f.write(encrypted_data)
    
    # Guardar clave AES cifrada en archivo separado
    # Generar nombre del archivo de clave basado en el output_path
    base_name = os.path.splitext(output_path)[0]
    key_output_path = base_name + '_encrypted_key.bin'
    with open(key_output_path, 'wb') as f:
        f.write(encrypted_aes_key)
    
    return key_output_path


def decrypt_image_hybrid(encrypted_image_path, encrypted_key_path, private_key_path, output_path):
    """
    Descifra una imagen cifrada usando cifrado híbrido.
    
    Flujo:
    1. Descifra la clave AES con RSA-1024 usando la clave privada
    2. Descifra la imagen con AES-128 usando la clave descifrada
    3. Guarda la imagen descifrada
    
    Args:
        encrypted_image_path: Ruta a la imagen cifrada
        encrypted_key_path: Ruta al archivo con la clave AES cifrada
        private_key_path: Ruta a la clave privada RSA
        output_path: Ruta donde guardar la imagen descifrada
        
    Returns:
        PIL.Image: Imagen descifrada
    """
    # Cargar datos cifrados
    with open(encrypted_image_path, 'rb') as f:
        encrypted_data = f.read()
    
    # Extraer dimensiones, IV y datos cifrados
    # Formato: 4 bytes width + 4 bytes height + 16 bytes IV + datos cifrados
    width = int.from_bytes(encrypted_data[0:4], byteorder='big')
    height = int.from_bytes(encrypted_data[4:8], byteorder='big')
    iv = encrypted_data[8:24]
    encrypted_image = encrypted_data[24:]
    
    # Descifrar la clave AES con RSA-1024
    private_key = load_rsa_private_key(private_key_path)
    with open(encrypted_key_path, 'rb') as f:
        encrypted_aes_key = f.read()
    
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Descifrar imagen con AES-128-CBC
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_image) + decryptor.finalize()
    
    # Quitar padding
    unpadder = padding.PKCS7(128).unpadder()
    img_bytes = unpadder.update(padded_data)
    img_bytes += unpadder.finalize()
    
    # Convertir bytes a imagen
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    # Reconstruir dimensiones usando las dimensiones guardadas
    img_array = img_array.reshape((height, width))
    
    img = Image.fromarray(img_array, mode='L')
    img.save(output_path)
    
    return img


def encrypt_image_with_mode(image_path, public_key_path, output_path, mode_name='CBC'):
    """
    Cifra una imagen usando cifrado híbrido con el modo AES especificado.
    
    Modos soportados: ECB, CBC, CTR, CFB, OCB
    
    Args:
        image_path: Ruta a la imagen a cifrar
        public_key_path: Ruta a la clave pública RSA
        output_path: Ruta donde guardar la imagen cifrada
        mode_name: Modo AES a usar ('ECB', 'CBC', 'CTR', 'CFB', 'OCB')
        
    Returns:
        tuple: (ruta_clave_cifrada, metadata_dict)
    """
    # Cargar imagen y convertir a bytes
    img = Image.open(image_path)
    width, height = img.size
    img_array = np.array(img)
    img_bytes = img_array.tobytes()
    
    # Generar clave AES-128
    aes_key = generate_aes_key()
    
    # Configurar modo según el parámetro
    mode_name = mode_name.upper()
    metadata = {'width': width, 'height': height, 'mode': mode_name}
    
    if mode_name == 'ECB':
        # ECB no necesita IV
        mode = modes.ECB()
        needs_padding = True
        iv_or_nonce = None
    elif mode_name == 'CBC':
        # CBC necesita IV de 16 bytes
        iv_or_nonce = os.urandom(16)
        mode = modes.CBC(iv_or_nonce)
        needs_padding = True
        metadata['iv'] = iv_or_nonce
    elif mode_name == 'CTR':
        # CTR necesita nonce de 16 bytes (8 bytes nonce + 8 bytes counter)
        iv_or_nonce = os.urandom(16)
        mode = modes.CTR(iv_or_nonce)
        needs_padding = False
        metadata['nonce'] = iv_or_nonce
    elif mode_name == 'CFB':
        # CFB necesita IV de 16 bytes
        iv_or_nonce = os.urandom(16)
        mode = modes.CFB(iv_or_nonce)
        needs_padding = False
        metadata['iv'] = iv_or_nonce
    elif mode_name == 'OCB':
        # OCB usa PyCryptodome (cryptography no soporta OCB)
        if not PYCRYPTODOME_AVAILABLE:
            raise ValueError("OCB requiere pycryptodome. Instala con: pip install pycryptodome")
        # OCB necesita nonce de 1 a 15 bytes (usamos 15 para máxima seguridad)
        iv_or_nonce = get_random_bytes(15)
        needs_padding = False
        metadata['nonce'] = iv_or_nonce
        mode = None  # OCB se maneja por separado con PyCryptodome
    else:
        raise ValueError(f"Modo no soportado: {mode_name}. Use: ECB, CBC, CTR, CFB, OCB")
    
    # Preparar datos
    if needs_padding:
        padder = padding.PKCS7(128).padder()
        data_to_encrypt = padder.update(img_bytes)
        data_to_encrypt += padder.finalize()
    else:
        data_to_encrypt = img_bytes
    
    # Cifrar imagen con AES-128
    if mode_name == 'OCB':
        # OCB usa PyCryptodome
        cipher_ocb = CryptoAES.new(aes_key, CryptoAES.MODE_OCB, nonce=iv_or_nonce)
        encrypted_image, tag = cipher_ocb.encrypt_and_digest(data_to_encrypt)
        metadata['tag'] = tag
    else:
        cipher = Cipher(algorithms.AES(aes_key), mode, backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_image = encryptor.update(data_to_encrypt) + encryptor.finalize()
    
    # Cifrar la clave AES con RSA-1024
    public_key = load_rsa_public_key(public_key_path)
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Guardar imagen cifrada con metadata
    # Formato simplificado: width(4) + height(4) + mode(3) + iv/nonce/tag_length + iv/nonce + datos + tag(OCB)
    width_bytes = width.to_bytes(4, byteorder='big')
    height_bytes = height.to_bytes(4, byteorder='big')
    mode_bytes = mode_name.encode('ascii').ljust(3, b'\x00')
    
    # Construir header básico
    header = width_bytes + height_bytes + mode_bytes
    
    # Agregar IV/nonce según el modo
    if mode_name == 'ECB':
        # ECB no tiene IV
        header += b'\x00\x00'  # longitud 0
    elif mode_name == 'CBC' or mode_name == 'CFB':
        # IV de 16 bytes
        header += (16).to_bytes(2, byteorder='big')
        header += iv_or_nonce
    elif mode_name == 'CTR':
        # Nonce de 16 bytes
        header += (16).to_bytes(2, byteorder='big')
        header += iv_or_nonce
    elif mode_name == 'OCB':
        # Nonce de 15 bytes (PyCryptodome OCB usa nonce de 1-15 bytes)
        header += (15).to_bytes(2, byteorder='big')
        header += iv_or_nonce
    
    # Agregar datos cifrados
    # Para OCB, necesitamos agregar el tag por separado (16 bytes al final)
    if mode_name == 'OCB':
        encrypted_data = header + encrypted_image + tag
    else:
        encrypted_data = header + encrypted_image
    
    with open(output_path, 'wb') as f:
        f.write(encrypted_data)
    
    # Guardar clave AES cifrada
    base_name = os.path.splitext(output_path)[0]
    key_output_path = base_name + '_encrypted_key.bin'
    with open(key_output_path, 'wb') as f:
        f.write(encrypted_aes_key)
    
    return key_output_path, metadata


def decrypt_image_with_mode(encrypted_image_path, encrypted_key_path, private_key_path, output_path):
    """
    Descifra una imagen cifrada usando el modo AES almacenado en el archivo.
    
    Args:
        encrypted_image_path: Ruta a la imagen cifrada
        encrypted_key_path: Ruta al archivo con la clave AES cifrada
        private_key_path: Ruta a la clave privada RSA
        output_path: Ruta donde guardar la imagen descifrada
        
    Returns:
        PIL.Image: Imagen descifrada
    """
    # Cargar datos cifrados
    with open(encrypted_image_path, 'rb') as f:
        encrypted_data = f.read()
    
    # Leer header: width(4) + height(4) + mode(3) + iv_len(2) + iv/nonce + datos + tag(OCB)
    width = int.from_bytes(encrypted_data[0:4], byteorder='big')
    height = int.from_bytes(encrypted_data[4:8], byteorder='big')
    mode_name = encrypted_data[8:11].rstrip(b'\x00').decode('ascii')
    iv_len = int.from_bytes(encrypted_data[11:13], byteorder='big')
    
    # Leer IV/nonce
    header_end = 13 + iv_len
    if iv_len > 0:
        iv_or_nonce = encrypted_data[13:header_end]
    else:
        iv_or_nonce = None
    
    # Determinar dónde empiezan los datos cifrados
    # Para OCB, el tag está al final del archivo (últimos 16 bytes)
    tag = None
    if mode_name == 'OCB':
        tag = encrypted_data[-16:]
        encrypted_image = encrypted_data[header_end:-16]
    else:
        encrypted_image = encrypted_data[header_end:]
    
    # Descifrar la clave AES con RSA-1024
    private_key = load_rsa_private_key(private_key_path)
    with open(encrypted_key_path, 'rb') as f:
        encrypted_aes_key = f.read()
    
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Configurar modo según el modo leído
    needs_padding = mode_name in ['ECB', 'CBC']
    
    if mode_name == 'OCB':
        # OCB usa PyCryptodome
        if not PYCRYPTODOME_AVAILABLE:
            raise ValueError("OCB requiere pycryptodome. Instala con: pip install pycryptodome")
        # Descifrar con PyCryptodome
        cipher_ocb = CryptoAES.new(aes_key, CryptoAES.MODE_OCB, nonce=iv_or_nonce)
        try:
            decrypted_data = cipher_ocb.decrypt_and_verify(encrypted_image, tag)
        except ValueError as e:
            raise ValueError(f"Error al descifrar con OCB: {str(e)}. "
                           f"El tag de autenticación no es válido.")
    else:
        # Otros modos usan cryptography
        if mode_name == 'ECB':
            mode = modes.ECB()
        elif mode_name == 'CBC':
            mode = modes.CBC(iv_or_nonce)
        elif mode_name == 'CTR':
            mode = modes.CTR(iv_or_nonce)
        elif mode_name == 'CFB':
            mode = modes.CFB(iv_or_nonce)
        else:
            raise ValueError(f"Modo no soportado: {mode_name}")
        
        # Descifrar imagen con AES-128
        cipher = Cipher(algorithms.AES(aes_key), mode, backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_image) + decryptor.finalize()
    
    # Quitar padding si es necesario
    if needs_padding:
        unpadder = padding.PKCS7(128).unpadder()
        img_bytes = unpadder.update(decrypted_data)
        img_bytes += unpadder.finalize()
    else:
        img_bytes = decrypted_data
    
    # Convertir bytes a imagen
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    img_array = img_array.reshape((height, width))
    
    img = Image.fromarray(img_array, mode='L')
    img.save(output_path)
    
    return img

