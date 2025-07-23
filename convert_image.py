import base64
import os

def image_to_base64(image_path):
    """Convert image to base64 string"""
    try:
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        print(f"Error converting image: {e}")
        return None

# The user's image should be saved as minecraft_backg.jpg or similar
# Let's check for common image formats
image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
base_path = r"c:\Users\MersYeon\Documents\My Server Wrapper"

for ext in image_extensions:
    image_path = os.path.join(base_path, f"minecraft_backg{ext}")
    if os.path.exists(image_path):
        print(f"Found image: {image_path}")
        base64_string = image_to_base64(image_path)
        if base64_string:
            # Determine MIME type
            mime_type = "image/jpeg" if ext.lower() in ['.jpg', '.jpeg'] else f"image/{ext[1:]}"
            data_url = f"data:{mime_type};base64,{base64_string}"
            
            # Save to file for easy copying
            with open(os.path.join(base_path, "background_base64.txt"), 'w') as f:
                f.write(data_url)
            
            print(f"Base64 conversion complete! Saved to background_base64.txt")
            print(f"MIME type: {mime_type}")
            print(f"Data URL length: {len(data_url)} characters")
            break
else:
    print("No image file found. Please save the Minecraft image as 'minecraft_backg.jpg' in the server wrapper directory.")