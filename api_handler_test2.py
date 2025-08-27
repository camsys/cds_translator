from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

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
                                   prompt_file="prompt1.txt", image_path="beach_st_signs/118.jpg"):
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
                              prompt_file="prompt2.txt", image_path="beach_st_signs/118.jpg"):
        """Make the second API call with system instructions2, prompt2, and image"""
        
        # Load the text files
        system_instruction = self.load_file_content(system_instruction_file)
        prompt = self.load_file_content(prompt_file)
        
        # Upload the image
        uploaded_file = self.upload_image(image_path)
        
        # Make the API call with image and prompt2
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            contents=[uploaded_file, prompt],  # Both image and prompt2.txt
        )
        
        return response.text
    
    def run_both_calls(self, image_path="beach_st_signs/118.jpg"):
        """Run both API calls in sequence and return both results"""
        
        print("Making first API call...")
        first_result = self.generate_content_with_prompt(image_path=image_path)
        
        print("First call completed. Making second API call...")
        second_result = self.generate_second_content(image_path=image_path)
        
        return {
            "first_call_result": first_result,
            "second_call_result": second_result
        }

# How to use your updated class:
if __name__ == "__main__":
    # Create your API manager
    api_manager = GeminiAPIManager()
    
    # Run both API calls
    results = api_manager.run_both_calls()
    
    # Print both results
    print("\n" + "="*50)
    print("FIRST API CALL RESULT:")
    print("="*50)
    print(results["first_call_result"])
    
    print("\n" + "="*50)
    print("SECOND API CALL RESULT:")
    print("="*50)
    print(results["second_call_result"])