import os
import sys
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.dataset_loader import load_dataset
from src.preprocessing import preprocess

# Change to project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)

# Load minimal dataset
images, labels = load_dataset("data")

# Create output directories
os.makedirs("data/processed/healthy", exist_ok=True)
os.makedirs("data/processed/tumor", exist_ok=True)

# Apply preprocessing and save
processed_images = []
for i, (img, label) in enumerate(zip(images, labels)):
    processed_img = preprocess(img)
    processed_images.append(processed_img)
    
    # Save processed image
    output_path = f"data/processed/{label}/image_{i:04d}.png"
    processed_img.save(output_path)
    print(f"Saved: {output_path}")

print(f"\nTotal images processed: {len(processed_images)}")

# Visual check (if there are images)
if len(images) > 0:
    plt.figure(figsize=(8,4))

    plt.subplot(1,2,1)
    plt.imshow(images[0], cmap="gray")
    plt.title("Original")

    plt.subplot(1,2,2)
    plt.imshow(processed_images[0], cmap="gray")
    plt.title("Preprocessed")

    plt.show()
