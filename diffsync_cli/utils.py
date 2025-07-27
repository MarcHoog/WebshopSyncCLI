import base64

def normalize_string(string: str):
    return string.strip().lower()


def base64_endcode_image(path):
    with open(path, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string
