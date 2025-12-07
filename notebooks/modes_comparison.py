"""
Script de comparación de los 5 modos AES (ECB, CBC, CTR, CFB, OCB).
Cifra la misma imagen con cada modo y muestra comparaciones visuales y métricas.
"""

import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hybrid_encryption import (
    generate_rsa_keypair,
    save_rsa_keys,
    encrypt_image_with_mode,
    decrypt_image_with_mode
)

# Change to project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)

# Crear directorios necesarios
os.makedirs("keys", exist_ok=True)
os.makedirs("data/encrypted/modes", exist_ok=True)
os.makedirs("data/decrypted/modes", exist_ok=True)

print("=" * 70)
print("COMPARACIÓN DE MODOS AES (ECB, CBC, CTR, CFB, OCB)")
print("=" * 70)

# Paso 1: Generar par de claves RSA-1024 (si no existen)
if not os.path.exists("keys/private_key.pem"):
    print("\n1. Generando par de claves RSA-1024...")
    private_key, public_key = generate_rsa_keypair()
    save_rsa_keys(private_key, public_key)
    print("   ✓ Claves RSA generadas y guardadas en 'keys/'")
else:
    print("\n1. Usando claves RSA existentes...")
    print("   ✓ Claves RSA encontradas en 'keys/'")

# Paso 2: Seleccionar una imagen procesada para cifrar
print("\n2. Seleccionando imagen para cifrar...")
processed_images_dir = "data/processed/healthy"
image_files = [f for f in os.listdir(processed_images_dir) if f.endswith('.png')]

if not image_files:
    print("   ✗ No se encontraron imágenes procesadas. Ejecuta preprocessing_demo.py primero.")
    sys.exit(1)

test_image = os.path.join(processed_images_dir, image_files[0])
print(f"   ✓ Imagen seleccionada: {test_image}")

# Cargar imagen original para comparación
original_img = Image.open(test_image)
original_size = os.path.getsize(test_image)

# Paso 3: Cifrar con los 5 modos
modes = ['ECB', 'CBC', 'CTR', 'CFB', 'OCB']
results = {}

print("\n3. Cifrando imagen con los 5 modos AES...")
print("-" * 70)

for mode in modes:
    print(f"\n   Modo: {mode}")
    try:
        start_time = time.time()
        
        encrypted_path = f"data/encrypted/modes/image_{mode.lower()}.bin"
        key_path, metadata = encrypt_image_with_mode(
            test_image,
            "keys/public_key.pem",
            encrypted_path,
            mode_name=mode
        )
        
        encrypt_time = time.time() - start_time
        encrypted_size = os.path.getsize(encrypted_path)
        key_size = os.path.getsize(key_path)
        
        # Descifrar para verificar
        start_time = time.time()
        decrypted_path = f"data/decrypted/modes/image_{mode.lower()}_decrypted.png"
        decrypted_img = decrypt_image_with_mode(
            encrypted_path,
            key_path,
            "keys/private_key.pem",
            decrypted_path
        )
        decrypt_time = time.time() - start_time
        
        # Verificar que la imagen descifrada sea idéntica
        original_array = np.array(original_img)
        decrypted_array = np.array(decrypted_img)
        is_identical = np.array_equal(original_array, decrypted_array)
        
        results[mode] = {
            'encrypt_time': encrypt_time,
            'decrypt_time': decrypt_time,
            'encrypted_size': encrypted_size,
            'key_size': key_size,
            'total_size': encrypted_size + key_size,
            'is_identical': is_identical,
            'encrypted_path': encrypted_path,
            'decrypted_path': decrypted_path
        }
        
        print(f"      ✓ Cifrado: {encrypt_time*1000:.2f} ms")
        print(f"      ✓ Descifrado: {decrypt_time*1000:.2f} ms")
        print(f"      ✓ Tamaño cifrado: {encrypted_size:,} bytes")
        print(f"      ✓ Verificación: {'✓ OK' if is_identical else '✗ FALLO'}")
        
    except Exception as e:
        print(f"      ✗ Error: {str(e)}")
        results[mode] = {'error': str(e)}

print("\n" + "=" * 70)
print("RESUMEN DE RESULTADOS")
print("=" * 70)

# Crear tabla de resultados
print("\n{:<8} {:<12} {:<12} {:<15} {:<15} {:<10}".format(
    "Modo", "Cifrado (ms)", "Descifrado (ms)", "Tamaño (bytes)", "Total (bytes)", "Estado"
))
print("-" * 70)

for mode in modes:
    if 'error' not in results[mode]:
        r = results[mode]
        status = "✓ OK" if r['is_identical'] else "✗ FALLO"
        print("{:<8} {:<12.2f} {:<12.2f} {:<15,} {:<15,} {:<10}".format(
            mode,
            r['encrypt_time'] * 1000,
            r['decrypt_time'] * 1000,
            r['encrypted_size'],
            r['total_size'],
            status
        ))
    else:
        print("{:<8} {:<50} {:<10}".format(mode, f"Error: {results[mode]['error']}", "✗ ERROR"))

# Visualización comparativa
print("\n4. Generando visualización comparativa...")

fig = plt.figure(figsize=(20, 12))

# Fila 1: Imagen original
ax = plt.subplot(3, 6, 1)
ax.imshow(original_img, cmap='gray')
ax.set_title("Original", fontsize=12, fontweight='bold')
ax.axis('off')

# Filas 2-3: Imágenes cifradas y descifradas para cada modo
for idx, mode in enumerate(modes):
    col = idx + 1
    
    if 'error' not in results[mode]:
        # Imagen cifrada (mostrar como ruido)
        ax = plt.subplot(3, 6, 6 + col)
        try:
            with open(results[mode]['encrypted_path'], 'rb') as f:
                encrypted_data = f.read()
            # Leer header y mostrar datos cifrados
            header_size = 13 + int.from_bytes(encrypted_data[11:13], byteorder='big')
            if mode == 'OCB':
                encrypted_preview = encrypted_data[header_size:-16]  # Excluir tag
            else:
                encrypted_preview = encrypted_data[header_size:]
            
            # Mostrar una porción como imagen
            preview_size = min(500*500, len(encrypted_preview))
            if preview_size == 500*500:
                encrypted_array = np.frombuffer(encrypted_preview[:preview_size], dtype=np.uint8)
                encrypted_array = encrypted_array.reshape((500, 500))
                ax.imshow(encrypted_array, cmap='gray')
            else:
                ax.text(0.5, 0.5, 'Datos cifrados', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=10)
        except:
            ax.text(0.5, 0.5, 'Error', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=10)
        ax.set_title(f"{mode}\n(Cifrado)", fontsize=10)
        ax.axis('off')
        
        # Imagen descifrada
        ax = plt.subplot(3, 6, 12 + col)
        try:
            decrypted_img = Image.open(results[mode]['decrypted_path'])
            ax.imshow(decrypted_img, cmap='gray')
            status = "✓" if results[mode]['is_identical'] else "✗"
            ax.set_title(f"{mode}\n(Descifrado) {status}", fontsize=10)
        except:
            ax.text(0.5, 0.5, 'Error', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=10)
        ax.axis('off')
    else:
        # Mostrar error
        for row_offset in [6, 12]:
            ax = plt.subplot(3, 6, row_offset + col)
            ax.text(0.5, 0.5, f'{mode}\nERROR', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=10, color='red')
            ax.axis('off')

plt.tight_layout()
comparison_path = "data/modes_comparison.png"
plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
print(f"   ✓ Comparación visual guardada en: {comparison_path}")

# Gráfico de rendimiento
print("\n5. Generando gráfico de rendimiento...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

modes_ok = [m for m in modes if 'error' not in results[m]]
encrypt_times = [results[m]['encrypt_time'] * 1000 for m in modes_ok]
decrypt_times = [results[m]['decrypt_time'] * 1000 for m in modes_ok]
sizes = [results[m]['total_size'] for m in modes_ok]

# Gráfico de tiempos
x = np.arange(len(modes_ok))
width = 0.35
ax1.bar(x - width/2, encrypt_times, width, label='Cifrado', color='#3498db')
ax1.bar(x + width/2, decrypt_times, width, label='Descifrado', color='#e74c3c')
ax1.set_xlabel('Modo AES')
ax1.set_ylabel('Tiempo (ms)')
ax1.set_title('Rendimiento: Tiempo de Cifrado/Descifrado')
ax1.set_xticks(x)
ax1.set_xticklabels(modes_ok)
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

# Gráfico de tamaños
ax2.bar(modes_ok, sizes, color='#2ecc71')
ax2.set_xlabel('Modo AES')
ax2.set_ylabel('Tamaño Total (bytes)')
ax2.set_title('Tamaño de Archivos Cifrados')
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
performance_path = "data/modes_performance.png"
plt.savefig(performance_path, dpi=150, bbox_inches='tight')
print(f"   ✓ Gráfico de rendimiento guardado en: {performance_path}")

print("\n" + "=" * 70)
print("COMPARACIÓN COMPLETADA")
print("=" * 70)
print("\nResumen:")
print("  • Se cifró la misma imagen con los 5 modos AES")
print("  • Se compararon tiempos de cifrado/descifrado")
print("  • Se compararon tamaños de archivos")
print("  • Se verificó la integridad de las imágenes descifradas")
print("\nArchivos generados:")
print(f"  • Comparación visual: {comparison_path}")
print(f"  • Gráfico de rendimiento: {performance_path}")

