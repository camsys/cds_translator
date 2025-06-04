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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                system_instruction="""You are a Curb Data Specification  (CDS) robot.  All you do is read signs and  write the policies into CDS.  If there are multiple signs, write multiple objects in the results.   

{
  "type": "object",
  "properties": {
    "curb_policy_id": {
      "type": "string",
      "description": "An ID that uniquely identifies this exact regulation across Curb Zones. Two Policy objects containing the same curb_policy_id MUST be completely identical. A curb_policy_id MUST NOT be reused. Once created, it must continue to refer to the identical policy forever."
    },
    "published_date": {
      "type": "integer",
      "format": "int64",
      "description": "The date/time that this policy was first published in this data feed. An integer representing a number of milliseconds since midnight, January 1st, 1970 UTC (the UNIX epoch)",
      "minimum": 0,
      "example": 1643130000000
    },
    "priority": {
      "type": "integer",
      "description": "Specifies which other policies this one takes precedence over. If two Policies on the same Curb Zone have overlapping Time Spans and apply to the same user class, the one that applies at a given time is the one with the lowest priority."
    },
    "rules": {
      "type": "array",
      "description": "The rule(s) that this policy applies.",
      "items": {
        "type": "object",
        "description": "A rule defines who is allowed to do what, and for how long, on a curb, per the policy.",
        "properties": {
          "activity": {
            "type": "string",
            "description": "The activity that is forbidden or permitted by this regulation.",
            "enum": [
              "parking",
              "no parking",
              "loading",
              "no loading",
              "unloading",
              "no unloading",
              "stopping",
              "no stopping",
              "travel",
              "no travel"
            ]
          },
          "max_stay": {
            "type": "integer",
            "description": "The length of time (in units of max_stay_unit) for which the curb may be used under this regulation. If not specified, the curb may be used under this regulation indefinitely."
          },
          "max_stay_unit": {
            "type": "string",
            "description": "An enumeration for units of time.",
            "enum": [
              "second",
              "minute",
              "hour",
              "day",
              "week",
              "month",
              "year"
            ]
          },
          "no_return": {
            "type": "integer",
            "description": "The length of time (in units of no_return_unit) that a user must vacate a Curb Zone before being allowed to return for another stay."
          },
          "no_return_unit": {
            "type": "string",
            "description": "The Unit of Time associated with the no_return value.",
            "enum": [
              "second",
              "minute",
              "hour",
              "day",
              "week",
              "month",
              "year"
            ]
          },
          "user_classes": {
            "type": "array",
            "description": "A user class represents any class of vehicles that is regulated by a city with respect to curb space.",
            "items": {
              "type": "string",
              "enum": [
                "bicycle",
                "bus",
                "cargo_bicycle",
                "car",
                "moped",
                "motorcycle",
                "scooter",
                "truck",
                "van",
                "handicap-accessible",
                "human",
                "electric_assist",
                "electric",
                "combustion",
                "autonomous",
                "construction",
                "delivery",
                "emergency_use",
                "freight",
                "parking",
                "permit",
                "rideshare",
                "school",
                "service_vehicles",
                "special_events",
                "taxi",
                "utilities",
                "vending",
                "waste_management"
              ]
            }
          },
          "rate": {
            "type": "array",
            "description": "The cost of using this Curb Zone when this regulation applies.",
            "items": {
              "type": "object",
              "properties": {
                "rate": {
                  "type": "integer",
                  "description": "The rate for this space in cents (or the smallest denomination of local currency) per rate_unit."
                },
                "rate_unit": {
                  "type": "string",
                  "description": "The unit of time associated with the rate.",
                  "enum": [
                    "second",
                    "minute",
                    "hour",
                    "day",
                    "week",
                    "month",
                    "year"
                  ]
                },
                "rate_unit_period": {
                  "type": "string",
                  "description": "The period of time that the rate_unit covers.",
                  "enum": [
                    "rolling",
                    "calendar"
                  ]
                },
                "increment_duration": {
                  "type": "integer",
                  "description": "If specified, this is the smallest number of rate_units a user can pay for."
                },
                "increment_amount": {
                  "type": "integer",
                  "description": "If specified, the rate for this space is rounded up to the nearest increment of this amount, specified in the same currency units as rate."
                },
                "start_duration": {
                  "type": "integer",
                  "description": "The number of rate_units the vehicle must have already been present in the Curb Zone before this rate starts applying."
                },
                "end_duration": {
                  "type": "integer",
                  "description": "The number of rate_units after which the rate stops applying."
                }
              },
              "required": [
                "rate",
                "rate_unit"
              ]
            }
          }
        },
        "required": [
          "activity"
        ]
      }
    },
    "time_spans": {
      "type": "array",
      "description": "If specified, this regulation only applies at the times defined within.",
      "items": {
        "type": "object",
        "description": "A time span defines a period of time (that may occur once or repeatedly) during which a given regulation applies. When multiple fields are combined, all criteria must be met in order for a given Time Span to apply. Note that, in order to specify, e.g., the "1st and 3rd Monday of the month", you can use days_of_month combined with days_of_week (in this example, days_of_week = ["mon"] and days_of_month = [1,2,3,4,5,6,7,15,16,17,18,19,20,21])",
        "properties": {
          "start_date": {
            "type": "integer",
            "format": "int64",
            "description": "The earliest point in time that this time span could apply (inclusive, see Range Boundaries). If unspecified, the Time Span applies to all matching periods arbitrarily far in the past. An integer representing a number of milliseconds since midnight, January 1st, 1970 UTC (the UNIX epoch)",
            "minimum": 0,
            "example": 1643130000000
          },
          "end_date": {
            "type": "integer",
            "format": "int64",
            "description": "The latest point in time that this time span could apply (exclusive, see Range Boundaries). If unspecified, the Time Span applies to all matching periods arbitrarily far in the future. See note below for more details. An integer representing a number of milliseconds since midnight, January 1st, 1970 UTC (the UNIX epoch)",
            "minimum": 0,
            "example": 1643130000000
          },
          "days_of_week": {
            "type": "array",
            "description": "An array of days of the week when this time span applies.",
            "items": {
              "type": "string",
              "enum": [
                "sun",
                "mon",
                "tue",
                "wed",
                "thu",
                "fri",
                "sat"
              ]
            }
          },
          "days_of_month": {
            "type": "array",
            "description": "An array of days of the month when this time span applies. An array of days of the month when this Time Span applies, specified as integers (1-31). Note that, in order to specify, e.g., the "1st and 3rd Monday of the month", you can use days_of_month combined with days_of_week (in this example, days_of_week = ["mon"] and days_of_month = [1,2,3,4,5,6,7,15,16,17,18,19,20,21]).",
            "items": {
              "type": "integer"
            }
          },
          "months": {
            "type": "array",
            "description": "If specified, this time span applies only during these months (1=January, 12=December).",
            "items": {
              "type": "integer",
              "minimum": 1,
              "maximum": 12
            }
          },
          "time_of_day_start": {
            "type": "string",
            "format": "time",
            "description": "The local time that this time span starts to apply, as 24-hour \"HH:MM\"."
          },
          "time_of_day_end": {
            "type": "string",
            "format": "time",
            "description": "The local time that this time span stops applying, as 24-hour \"HH:MM\"."
          },
          "designated_period": {
            "type": "string",
            "description": "A string representing an arbitrarily-named, externally-defined period of time.",
            "enum": [
              "snow emergency",
              "holidays",
              "school days",
              "game days"
            ]
          },
          "designated_period_except": {
            "type": "boolean",
            "description": "If specified and true, this time span applies at all times not matching the named designated period."
          }
        }
      }
    },
    "data_source_operator_id": {
      "type": "array",
      "description": "An array of Data Source Operator IDs that this policy only applies to. Values are defined globally and are managed by the Open Mobility Foundation and operators may register",
      "items": {
        "type": "string",
        "format": "uuid"
      }
    }
  },
  "required": [
    "curb_policy_id",
    "published_date",
    "priority",
    "rules"
  ]
}

"""),
            contents=[my_file, "Analyze the photo and give the CDS formatted policy"],
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