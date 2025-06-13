from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)

load_dotenv()

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("API_KEY"))

def load_si(file_path="system_instructions1.txt"):
    with open(file_path, 'r') as file:
        return file.read()

def load_prompt(file_path="prompt1.txt"):
    with open(file_path, 'r') as file:
        return file.read()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

si_data = load_si()
prompt_data = load_prompt()

def analyze_sign_image(image_path):
    """
    Your existing API logic wrapped in a function
    """
    try:
        # Upload file to Gemini
        my_file = client.files.upload(file=image_path)

        # Generate content with your existing system instruction
        response = client.models.generate_content(
          model="gemini-2.0-flash",

        config=types.GenerateContentConfig(
              system_instruction=si_data
              ),

          contents=[my_file, prompt_data],
        )
        
        return response.text
        
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

@app.route('/')
def home():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/analyze-sign', methods=['POST'])
def analyze_sign():
    """Handle image upload and analysis"""
    try:
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
            
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload an image.'}), 400
            
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
            
        # Analyze the image using your existing function
        result = analyze_sign_image(temp_path)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        # Return the CDS analysis result
        return jsonify({
            'success': True,
            'analysis': result,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

if __name__ == '__main__':
    app.run(debug=True)