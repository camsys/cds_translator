from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import tempfile
from werkzeug.utils import secure_filename

# GeminiAPIManager class built into the app
class GeminiAPIManager:
    def __init__(self, api_key=None):
        """Initialize the API manager with your Gemini client"""
        load_dotenv()  # Load environment variables
        
        # Use provided API key or get from environment
        if api_key is None:
            api_key = os.getenv("API_KEY")
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"  # Store model name for reuse
    
    def load_file_content(self, file_path):
        """Load content from a text file"""
        with open(file_path, 'r') as file:
            return file.read()
    
    def upload_image(self, image_path):
        """Upload an image file to Gemini"""
        return self.client.files.upload(file=image_path)
    
    def generate_content_with_prompt(self, system_instruction_file="system_instructions1.txt", 
                                   prompt_file="prompt1.txt", image_path=None):
        """Make the first API call with system instructions, prompt, and image"""
        
        # Load the text files
        system_instruction = self.load_file_content(system_instruction_file)
        prompt = self.load_file_content(prompt_file)
        
        # Upload the image
        uploaded_file = self.upload_image(image_path)
        
        # Make the API call
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            contents=[uploaded_file, prompt],
        )
        
        return response.text
    
    def generate_second_content(self, system_instruction_file="system_instructions2.txt", 
                              prompt_file="prompt2.txt", image_path=None,
                              vehicle_type=None, date=None, time=None):
        """Make the second API call with system instructions2, dynamic prompt, and image"""
        
        # Load the text files
        system_instruction = self.load_file_content(system_instruction_file)
        prompt_template = self.load_file_content(prompt_file)
        
        # Replace placeholders with actual values
        prompt = prompt_template.format(
            vehicle_type=vehicle_type or "Not specified",
            date=date or "Not specified", 
            time=time or "Not specified"
        )
        
        # Upload the image
        uploaded_file = self.upload_image(image_path)
        
        # Make the API call with image and dynamic prompt
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            contents=[uploaded_file, prompt],
        )
        
        return response.text
    
    def run_both_calls(self, image_path, vehicle_type=None, date=None, time=None):
        """Run both API calls in sequence and return both results"""

        try:
            first_result = self.generate_content_with_prompt(image_path=image_path)
            second_result = self.generate_second_content(
                image_path=image_path, 
                vehicle_type=vehicle_type, 
                date=date, 
                time=time
            )
        
            return {
                "first_call_result": first_result,
                "second_call_result": second_result
            }
        except Exception as e:
            return {
                "error": f"API call failed: {str(e)}",
                "first_call_result": None,
                "second_call_result": None
            }

# Flask app setup
app = Flask(__name__)

load_dotenv()

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/analyze-sign', methods=['POST'])
def analyze_sign():
    """Handle image upload and analysis with both API calls"""
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
            
        # Extract user input from the form
        vehicle_type = request.form.get('vehicle_type', 'car')
        date = request.form.get('date', '')
        time = request.form.get('time', '')

        # Create API manager and run both calls with user variables
        api_manager = GeminiAPIManager()
        results = api_manager.run_both_calls(temp_path, vehicle_type, date, time)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        # Check if there was an error
        if "error" in results:
            return jsonify({
                'success': False,
                'error': results["error"],
                'filename': filename
            }), 500
        
        # Return both analysis results
        return jsonify({
            'success': True,
            'first_analysis': results['first_call_result'],
            'second_analysis': results['second_call_result'],
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

