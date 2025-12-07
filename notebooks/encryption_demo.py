"""
Script de demostración del cifrado híbrido de imágenes médicas.
Muestra cómo cifrar y descifrar imágenes usando AES-128 + RSA-1024.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hybrid_encryption import (
    generate_rsa_keypair,
    save_rsa_keys,
    encrypt_image_hybrid,
    decrypt_image_hybrid
)

# Change to project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)

# Crear directorios necesarios
os.makedirs("keys", exist_ok=True)
os.makedirs("data/encrypted", exist_ok=True)
os.makedirs("data/decrypted", exist_ok=True)

print("=" * 60)
print("DEMOSTRACIÓN DE CIFRADO HÍBRIDO (AES-128 + RSA-1024)")
print("=" * 60)

# Paso 1: Generar par de claves RSA-1024
print("\n1. Generando par de claves RSA-1024...")
private_key, public_key = generate_rsa_keypair()
save_rsa_keys(private_key, public_key)
print("   ✓ Claves RSA generadas y guardadas en 'keys/'")

# Paso 2: Seleccionar una imagen procesada para cifrar
print("\n2. Seleccionando imagen para cifrar...")
processed_images_dir = "data/processed/healthy"
image_files = [f for f in os.listdir(processed_images_dir) if f.endswith('.png')]

if not image_files:
    print("   ✗ No se encontraron imágenes procesadas. Ejecuta preprocessing_demo.py primero.")
    sys.exit(1)

test_image = os.path.join(processed_images_dir, image_files[0])
print(f"   ✓ Imagen seleccionada: {test_image}")

# Paso 3: Cifrar la imagen
print("\n3. Cifrando imagen con AES-128 + RSA-1024...")
encrypted_image_path = "data/encrypted/image_encrypted.bin"
encrypted_key_path = encrypt_image_hybrid(
    test_image,
    "keys/public_key.pem",
    encrypted_image_path
)
print(f"   ✓ Imagen cifrada guardada en: {encrypted_image_path}")
print(f"   ✓ Clave AES cifrada guardada en: {encrypted_key_path}")

# Mostrar tamaño de archivos
original_size = os.path.getsize(test_image)
encrypted_size = os.path.getsize(encrypted_image_path)
key_size = os.path.getsize(encrypted_key_path)
print(f"\n   Tamaños:")
print(f"   - Original: {original_size:,} bytes")
print(f"   - Cifrada: {encrypted_size:,} bytes")
print(f"   - Clave cifrada: {key_size:,} bytes")

# Paso 4: Descifrar la imagen
print("\n4. Descifrando imagen...")
decrypted_image_path = "data/decrypted/image_decrypted.png"
decrypted_img = decrypt_image_hybrid(
    encrypted_image_path,
    encrypted_key_path,
    "keys/private_key.pem",
    decrypted_image_path
)
print(f"   ✓ Imagen descifrada guardada en: {decrypted_image_path}")

# Paso 5: Verificación visual
print("\n5. Verificación visual...")
from PIL import Image

original_img = Image.open(test_image)

plt.figure(figsize=(15, 5))

plt.subplot(1, 3, 1)
plt.imshow(original_img, cmap='gray')
plt.title("Imagen Original\n(Procesada)")
plt.axis('off')

plt.subplot(1, 3, 2)
# Mostrar datos cifrados como imagen (será ruido aleatorio)
with open(encrypted_image_path, 'rb') as f:
    encrypted_data = f.read()
# Mostrar solo una porción para visualización
encrypted_preview = encrypted_data[24:24+500*500]  # Saltar header y tomar primeros píxeles
if len(encrypted_preview) < 500*500:
    encrypted_preview = encrypted_data[24:24+len(encrypted_preview)]
encrypted_array = np.frombuffer(encrypted_preview[:500*500], dtype=np.uint8)
if len(encrypted_array) == 500*500:
    encrypted_array = encrypted_array.reshape((500, 500))
    plt.imshow(encrypted_array, cmap='gray')
else:
    plt.text(0.5, 0.5, 'Datos cifrados\n(ruido aleatorio)', 
             ha='center', va='center', transform=plt.gca().transAxes)
plt.title("Imagen Cifrada\n(Datos encriptados)")
plt.axis('off')

plt.subplot(1, 3, 3)
plt.imshow(decrypted_img, cmap='gray')
plt.title("Imagen Descifrada")
plt.axis('off')

plt.tight_layout()
plt.savefig("data/encryption_comparison.png", dpi=150, bbox_inches='tight')
print("   ✓ Comparación visual guardada en: data/encryption_comparison.png")

# Verificar que las imágenes son idénticas
original_array = np.array(original_img)
decrypted_array = np.array(decrypted_img)

if np.array_equal(original_array, decrypted_array):
    print("\n   ✓ VERIFICACIÓN EXITOSA: La imagen descifrada es idéntica a la original")
else:
    print("\n   ⚠ ADVERTENCIA: Las imágenes no son idénticas (puede ser por diferencias de formato)")

print("\n" + "=" * 60)
print("DEMOSTRACIÓN COMPLETADA")
print("=" * 60)
print("\nResumen del cifrado híbrido:")
print("  • AES-128: Cifra la imagen (rápido para datos grandes)")
print("  • RSA-1024: Cifra la clave AES (seguro para intercambio)")
print("  • La clave AES se genera aleatoriamente para cada imagen")
print("  • Solo quien tiene la clave privada RSA puede descifrar")

