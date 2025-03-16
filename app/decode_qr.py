import cv2
from pyzbar.pyzbar import decode

# Load the QR code image
image = cv2.imread("image.png")  # Update with your file path if needed

# Decode the QR code
decoded_objects = decode(image)

# Print the extracted data
for obj in decoded_objects:
    print("Decoded Data:", obj.data.decode("utf-8"))
