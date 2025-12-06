A lightweight local version of the preprocessing pipeline was created to replicate the initial configuration of the original project. A minimal dataset of six MRI images (ten healthy and ten with tumor) was organized into two folders. Two Python modules were developed:

1. dataset_loader.py: loads images from the dataset and assigns class labels.
2. preprocessing.py: applies a center crop and resizes each image to 256×256 pixels.

A demonstration script verifies the preprocessing workflow by displaying original and transformed images. This setup allows testing and validating the preprocessing pipeline entirely on a local laptop without requiring the full dataset.
