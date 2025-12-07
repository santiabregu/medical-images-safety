# Sistema de Cifrado Híbrido para Imágenes Médicas

Sistema de cifrado híbrido que utiliza **AES-128** + **RSA-1024** para proteger imágenes médicas (MRI). El proyecto implementa y compara **5 modos de operación AES**: ECB, CBC, CTR, CFB y OCB.

## 📋 Descripción

Este proyecto implementa un sistema de cifrado híbrido diseñado específicamente para proteger imágenes médicas. El sistema combina:

- **AES-128**: Cifrado simétrico rápido para cifrar las imágenes (5 modos de operación)
- **RSA-1024**: Cifrado asimétrico para proteger la clave AES

### Modos AES Implementados

1. **ECB (Electronic Codebook)**: Modo básico sin IV, requiere padding
2. **CBC (Cipher Block Chaining)**: Modo con IV de 16 bytes, requiere padding
3. **CTR (Counter)**: Modo con nonce de 16 bytes, sin padding
4. **CFB (Cipher Feedback)**: Modo con IV de 16 bytes, sin padding
5. **OCB (Offset Codebook)**: Modo autenticado con nonce de 15 bytes, sin padding (usa PyCryptodome)

## 🏗️ Estructura del Proyecto

```
medical-images-safety/
├── data/
│   ├── healthy/          # Imágenes originales sanas
│   ├── tumor/            # Imágenes originales con tumor
│   ├── processed/        # Imágenes procesadas
│   ├── encrypted/        # Imágenes cifradas (generado automáticamente)
│   └── decrypted/        # Imágenes descifradas (generado automáticamente)
├── keys/                 # Claves RSA (generado automáticamente)
│   ├── private_key.pem   # Clave privada RSA-1024
│   └── public_key.pem    # Clave pública RSA-1024
├── notebooks/
│   ├── preprocessing_demo.py    # Demo de preprocesamiento
│   ├── encryption_demo.py        # Demo de cifrado básico
│   └── modes_comparison.py      # Comparación de los 5 modos AES
├── src/
│   ├── dataset_loader.py        # Carga de imágenes
│   ├── preprocessing.py         # Preprocesamiento de imágenes
│   └── hybrid_encryption.py     # Cifrado híbrido (AES-128 + RSA-1024)
├── requirements.txt
└── README.md
```

## 📦 Módulos

### 1. `dataset_loader.py`
Carga imágenes del dataset y asigna etiquetas de clase (healthy/tumor).

### 2. `preprocessing.py`
Aplica preprocesamiento a las imágenes:
- Center crop si la imagen es mayor a 500×500
- Redimensiona a 500×500 píxeles
- Convierte a escala de grises

### 3. `hybrid_encryption.py`
Implementa el cifrado híbrido con funciones para:
- Generar pares de claves RSA-1024
- Guardar/cargar claves RSA en formato PEM
- Cifrar imágenes con cualquier modo AES (ECB, CBC, CTR, CFB, OCB)
- Descifrar imágenes detectando automáticamente el modo usado

### 4. Gestión de Claves (`keys/`)
El directorio `keys/` se crea automáticamente y contiene:
- **`private_key.pem`**: Clave privada RSA-1024 (formato PEM, sin cifrar)
- **`public_key.pem`**: Clave pública RSA-1024 (formato PEM)

**⚠️ Importante**: 
- La clave privada debe mantenerse **secreta** y **nunca compartirse**
- La clave pública puede compartirse para cifrar datos
- Las claves se generan automáticamente al ejecutar los scripts de demo
- Si ya existen claves, los scripts las reutilizan

## 🔄 Flujo de Trabajo

### 1. Preprocesamiento
Las imágenes se procesan y normalizan:
- Center crop
- Redimensionado a 500×500 píxeles
- Conversión a escala de grises

### 2. Cifrado Híbrido
1. Se genera una clave AES-128 aleatoria para cada imagen
2. La imagen se cifra con AES-128 usando el modo seleccionado
3. La clave AES se cifra con RSA-1024 usando la clave pública
4. Se guardan: imagen cifrada + clave AES cifrada

### 3. Descifrado
1. Se descifra la clave AES con RSA-1024 usando la clave privada
2. Se descifra la imagen con AES-128 usando el modo detectado
3. Se verifica la integridad de la imagen descifrada

## 🚀 Instalación

```bash
pip install -r requirements.txt
```

### Dependencias

- `numpy`: Manipulación de arrays
- `pillow`: Procesamiento de imágenes
- `matplotlib`: Visualización
- `scikit-image`: Procesamiento avanzado de imágenes
- `opencv-python`: Operaciones de imagen
- `cryptography`: Cifrado (AES ECB, CBC, CTR, CFB)
- `pycryptodome`: Cifrado (AES OCB)

## 💻 Uso

### 1. Preprocesar imágenes

```bash
python notebooks/preprocessing_demo.py
```

Procesa las imágenes del dataset y las guarda en `data/processed/`.

### 2. Cifrado y descifrado básico

```bash
python notebooks/encryption_demo.py
```

Demuestra el cifrado híbrido usando el modo CBC por defecto.

### 3. Comparación de modos AES

```bash
python notebooks/modes_comparison.py
```

Cifra la misma imagen con los 5 modos AES y genera:
- Tabla comparativa de rendimiento
- Visualización comparativa de imágenes cifradas/descifradas
- Gráficos de tiempos de cifrado/descifrado
- Gráficos de tamaños de archivos

## 📊 Características de los Modos AES

| Modo | IV/Nonce | Padding | Biblioteca | Características |
|------|----------|---------|------------|-----------------|
| **ECB** | No | Sí | cryptography | Simple, no recomendado para producción |
| **CBC** | 16 bytes | Sí | cryptography | Seguro, ampliamente usado |
| **CTR** | 16 bytes | No | cryptography | Paralelizable, eficiente |
| **CFB** | 16 bytes | No | cryptography | Permite cifrado por stream |
| **OCB** | 15 bytes | No | pycryptodome | Autenticado, más seguro |

## 🔐 Seguridad

- **AES-128**: Clave de 128 bits (16 bytes)
- **RSA-1024**: Claves de 1024 bits
- **Padding**: PKCS7 para modos que lo requieren
- **IV/Nonce**: Generados aleatoriamente para cada cifrado
- **Tag de autenticación**: OCB incluye tag de 16 bytes para verificación de integridad

## 📝 Notas

- El dataset incluye 20 imágenes de ejemplo (10 sanas, 10 con tumor)
- Las imágenes procesadas se guardan en formato PNG
- Las imágenes cifradas se guardan en formato binario
- Las claves RSA se guardan en formato PEM en el directorio `keys/`
- El directorio `keys/` se crea automáticamente al generar las claves
- OCB requiere `pycryptodome` ya que `cryptography` no lo soporta nativamente
- **Seguridad**: Nunca compartas la clave privada (`keys/private_key.pem`)

