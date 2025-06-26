const fileInput = document.getElementById('dropzone-file');
const imagePreview = document.getElementById('image-preview');
const uploadedImage = document.getElementById('uploaded-image');
const fileError = document.getElementById('file-error');
const analyzeButton = document.getElementById('analyze-button');
const resultDiv = document.getElementById('result');
const resultText = document.getElementById('result-text');
const canIParkHereSection = document.getElementById('can-i-park-here-section');
const canIParkHereContent = document.getElementById('can-i-park-here-content');
const cdsOutputSection = document.getElementById('cds-output-section');
const cdsJsonElement = document.getElementById('cds-json');

fileInput.addEventListener('change', handleFileChange);
analyzeButton.addEventListener('click', analyzeParkingRules);

function handleFileChange(event) {
    const file = event.target.files[0];

    if (file) {
        if (file.type.startsWith('image/')) {
            fileError.style.display = 'none';
            
            const reader = new FileReader();
            reader.onload = function(e) {
                uploadedImage.src = e.target.result;
                
                // Style the image for reasonable display
                uploadedImage.style.maxWidth = '400px';
                uploadedImage.style.maxHeight = '300px';
                uploadedImage.style.width = 'auto';
                uploadedImage.style.height = 'auto';
                uploadedImage.style.objectFit = 'contain'; // Prevents distortion
                uploadedImage.style.border = '2px solid #ddd';
                uploadedImage.style.borderRadius = '8px';
                uploadedImage.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                
                // Show the image preview
                imagePreview.style.display = 'block';
                
                // Hide the upload box (assuming it has an ID like 'upload-box' or 'dropzone')
                const uploadBox = document.getElementById('dropzone') || 
                                 document.querySelector('.dropzone') ||
                                 document.querySelector('[for="dropzone-file"]')?.parentElement;
                
                if (uploadBox) {
                    uploadBox.style.display = 'none';
                }
            }
            reader.readAsDataURL(file);
        } else {
            fileError.textContent = 'Invalid file type. Please upload an image.';
            fileError.style.display = 'block';
            imagePreview.style.display = 'none';
            fileInput.value = ''; // Clear the input
        }
    } else {
        fileError.style.display = 'none';
        imagePreview.style.display = 'none';
        
        // Show the upload box again if no file selected
        const uploadBox = document.getElementById('dropzone') || 
                         document.querySelector('.dropzone') ||
                         document.querySelector('[for="dropzone-file"]')?.parentElement;
        
        if (uploadBox) {
            uploadBox.style.display = 'block';
        }
    }
}


async function analyzeParkingRules() {
    const vehicleType = document.getElementById('vehicle-type').value;
    const date = document.getElementById('date').value;
    const time = document.getElementById('time').value;
    const imageFile = fileInput.files[0];

    if (!imageFile) {
        showUserMessage('Please upload an image of the parking sign.');
        return;
    }

    if (!date || !time) {
        showUserMessage('Please enter both date and time.');
        return;
    }

    // Show loading state
    analyzeButton.disabled = true;
    analyzeButton.textContent = 'Analyzing...';
    resultDiv.style.display = 'none';
    canIParkHereSection.style.display = 'none';
    cdsOutputSection.style.display = 'none';

    try {
        // Create FormData to send the image to Flask
        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('vehicle_type', vehicleType);
        formData.append('date', date);
        formData.append('time', time);

        // Call your Flask backend
        const response = await fetch('/analyze-sign', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze image');
        }

        if (data.success) {
            // Handle the FIRST API response (CDS Output Section)
            try {
                // Try to parse the first response as JSON for pretty formatting
                const firstResponseData = JSON.parse(data.first_analysis);
                cdsJsonElement.textContent = JSON.stringify(firstResponseData, null, 2);
            } catch (parseError) {
                // If it's not valid JSON, display as plain text
                cdsJsonElement.textContent = data.first_analysis;
            }

            // Handle the SECOND API response (Can I Park Here Section)
            const parkingResultHtml = `
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-gray-800 mb-2">Parking Analysis Result:</h4>
                    <div class="text-gray-700 whitespace-pre-wrap">${data.second_analysis}</div>
                </div>
            `;
            canIParkHereContent.innerHTML = parkingResultHtml;

            // Show both sections
            cdsOutputSection.style.display = 'block';
            canIParkHereSection.style.display = 'block';

        } else {
            throw new Error('Analysis failed');
        }

    } catch (error) {
        console.error('Error analyzing image:', error);
        showUserMessage(`Error analyzing image: ${error.message}`);
        
        // Hide result sections on error
        resultDiv.style.display = 'none';
        cdsOutputSection.style.display = 'none';
        canIParkHereSection.style.display = 'none';

    } finally {
        // Reset button state
        analyzeButton.disabled = false;
        analyzeButton.textContent = 'Analyze Parking Rules';
    }
}

// Custom message box function (replaces alert())
function showUserMessage(message) {
    // Create a simple modal/message box dynamically
    let messageBox = document.getElementById('custom-message-box');
    if (!messageBox) {
        messageBox = document.createElement('div');
        messageBox.id = 'custom-message-box';
        messageBox.className = 'fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center z-50';
        messageBox.innerHTML = `
            <div class="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full text-center">
                <p id="custom-message-text" class="text-gray-800 text-lg mb-4"></p>
                <button id="custom-message-ok" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                    OK
                </button>
            </div>
        `;
        document.body.appendChild(messageBox);
        document.getElementById('custom-message-ok').addEventListener('click', () => {
            messageBox.style.display = 'none';
        });
    }
    document.getElementById('custom-message-text').innerText = message;
    messageBox.style.display = 'flex';
}