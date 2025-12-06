from PIL import Image

def center_crop(img, size=500):
    width, height = img.size
    
    # Solo hacer crop si la imagen es más grande que el tamaño objetivo
    if width < size or height < size:
        return img
    
    left = (width - size) // 2
    top = (height - size) // 2
    right = left + size
    bottom = top + size

    return img.crop((left, top, right, bottom))


def preprocess(img, size=500):
    # Si la imagen es más grande, hacer center crop primero
    if img.size[0] > size or img.size[1] > size:
        cropped = center_crop(img, size)
    else:
        cropped = img
    
    # Resize para asegurar dimensiones exactas
    resized = cropped.resize((size, size), Image.Resampling.LANCZOS)
    return resized
