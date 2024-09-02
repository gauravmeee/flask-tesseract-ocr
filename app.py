import os
import logging
import tempfile
import subprocess
from flask import Flask, request, render_template, jsonify, send_file
from flask_cors import CORS
import pytesseract
from pytesseract import Output
from pytesseract.pytesseract import TesseractNotFoundError
import cv2

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure the output directory exists
output_dir = os.path.join(os.getcwd(), 'output')
os.makedirs(output_dir, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_image():
    try:
        # Debug information
        logger.debug(f"Tesseract version: {subprocess.check_output(['tesseract', '--version']).decode()}")
        logger.debug(f"Tesseract location: {subprocess.check_output(['which', 'tesseract']).decode()}")
        logger.debug(f"TESSDATA_PREFIX: {os.environ.get('TESSDATA_PREFIX', 'Not set')}")
        logger.debug(f"Current working directory: {os.getcwd()}")
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            # Save the uploaded file temporarily
            temp_filename = os.path.join(tempfile.gettempdir(), file.filename)
            file.save(temp_filename)
            
            # Perform OCR processing
            image = cv2.imread(temp_filename)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray)
            
            # Generate output image with bounding boxes
            output_filename = os.path.join(output_dir, 'output.jpg')
            output_image = draw_bounding_boxes(image, text)
            cv2.imwrite(output_filename, output_image)
            
            # Clean up the temporary file
            os.remove(temp_filename)
            
            return jsonify({
                'text': text,
                'image_url': '/output.jpg'
            })
        else:
            return jsonify({'error': 'File type not allowed'}), 400
    
    except TesseractNotFoundError as e:
        logger.error(f"Tesseract OCR not found: {str(e)}")
        return jsonify({
            'error': 'Tesseract OCR is not properly installed. Please contact support.'
        }), 500
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred. Please try again later.'
        }), 500

# Route for serving the output image
@app.route('/output.jpg', methods=['GET'])
def serve_output_image():
    output_filename = os.path.join(os.getcwd(), 'output.jpg')
    return send_file(output_filename, mimetype='image/jpeg')

def draw_bounding_boxes(img, text):
    d = pytesseract.image_to_data(img, output_type=Output.DICT)
    n_boxes = len(d['text'])
    for i in range(n_boxes):
        if int(d['conf'][i]) > 60:
            (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return img


if __name__ == '__main__':
    app.run(debug=True)