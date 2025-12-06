import os
from PIL import Image

def load_dataset(path):
    images = []
    labels = []

    for label in ["healthy", "tumor"]:
        class_dir = os.path.join(path, label)

        for filename in os.listdir(class_dir):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                img_path = os.path.join(class_dir, filename)
                img = Image.open(img_path).convert("L")  # grayscale

                images.append(img)
                labels.append(label)

    return images, labels
