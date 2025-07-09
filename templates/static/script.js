// Global variables
let video, video2, canvas, canvas2, ctx, ctx2;
let stream = null;
let capturedImages = [];

// DOM elements
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    video = document.getElementById('video');
    video2 = document.getElementById('video2');
    canvas = document.getElementById('canvas');
    canvas2 = document.getElementById('canvas2');
    ctx = canvas.getContext('2d');
    ctx2 = canvas2.getContext('2d');
    
    // Set canvas dimensions to match video
    function setCanvasDimensions() {
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        canvas2.width = video2.videoWidth || 640;
        canvas2.height = video2.videoHeight || 480;
    }
    
    // Event listeners for Register tab
    document.getElementById('startCamera').addEventListener('click', () => startCamera(video));
    document.getElementById('capture').addEventListener('click', captureImage);
    document.getElementById('registerBtn').addEventListener('click', registerPerson);
    
    // Event listeners for Recognize tab
    document.getElementById('startCamera2').addEventListener('click', () => startCamera(video2));
    document.getElementById('recognizeBtn').addEventListener('click', recognizeFace);
    
    // Initialize tabs
    const tabEl = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabEl.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            // Stop any existing streams when switching tabs
            if (stream) {
                stopCamera();
            }
            // Reset UI elements
            if (event.target.id === 'register-tab') {
                document.getElementById('capture').disabled = true;
                document.getElementById('registerBtn').disabled = true;
            } else if (event.target.id === 'recognize-tab') {
                document.getElementById('recognizeBtn').disabled = true;
            }
        });
    });
    
    // Set initial canvas dimensions
    setCanvasDimensions();
    window.addEventListener('resize', setCanvasDimensions);
});

// Start camera
async function startCamera(videoElement) {
    try {
        // Stop any existing stream
        if (stream) {
            stopCamera();
        }
        
        // Request camera access
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user' 
            }, 
            audio: false 
        });
        
        // Set video source
        videoElement.srcObject = stream;
        
        // Enable buttons after camera starts
        if (videoElement.id === 'video') {
            document.getElementById('capture').disabled = false;
        } else {
            document.getElementById('recognizeBtn').disabled = false;
        }
        
        // Update canvas dimensions when video metadata is loaded
        videoElement.onloadedmetadata = () => {
            setCanvasDimensions();
        };
        
    } catch (err) {
        console.error('Error accessing camera:', err);
        alert('Could not access the camera. Please ensure you have granted camera permissions.');
    }
}

// Stop camera
function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    if (video.srcObject) video.srcObject = null;
    if (video2.srcObject) video2.srcObject = null;
}

// Capture image from video
function captureImage() {
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
        // Draw current video frame to canvas
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Get image data as base64
        const imageData = canvas.toDataURL('image/jpeg');
        
        // Add to captured images array
        capturedImages.push(imageData);
        
        // Update preview
        updatePreview();
        
        // Enable register button if we have at least 3 images
        if (capturedImages.length >= 3) {
            document.getElementById('registerBtn').disabled = false;
        }
    }
}

// Update image preview
function updatePreview() {
    const preview = document.getElementById('preview');
    preview.innerHTML = '';
    
    capturedImages.forEach((img, index) => {
        const imgElement = document.createElement('img');
        imgElement.src = img;
        imgElement.className = 'captured-image';
        imgElement.alt = `Captured image ${index + 1}`;
        
        // Add delete button
        const container = document.createElement('div');
        container.style.position = 'relative';
        container.style.display = 'inline-block';
        
        const deleteBtn = document.createElement('button');
        deleteBtn.innerHTML = '×';
        deleteBtn.className = 'btn btn-sm btn-danger';
        deleteBtn.style.position = 'absolute';
        deleteBtn.style.top = '5px';
        deleteBtn.style.right = '5px';
        deleteBtn.style.padding = '0 5px';
        deleteBtn.style.borderRadius = '50%';
        deleteBtn.onclick = () => removeImage(index);
        
        container.appendChild(imgElement);
        container.appendChild(deleteBtn);
        preview.appendChild(container);
    });
}

// Remove captured image
function removeImage(index) {
    capturedImages.splice(index, 1);
    updatePreview();
    
    // Disable register button if we have less than 3 images
    if (capturedImages.length < 3) {
        document.getElementById('registerBtn').disabled = true;
    }
}

// Register a new person
async function registerPerson() {
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const statusElement = document.getElementById('status');
    
    if (!name) {
        statusElement.textContent = 'Please enter a name';
        statusElement.style.color = 'red';
        return;
    }
    
    if (capturedImages.length === 0) {
        statusElement.textContent = 'Please capture at least one image';
        statusElement.style.color = 'red';
        return;
    }
    
    try {
        statusElement.textContent = 'Registering...';
        statusElement.style.color = 'black';
        
        // Convert base64 images to files
        const formData = new FormData();
        formData.append('name', name);
        if (email) formData.append('email', email);
        
        capturedImages.forEach((img, index) => {
            const blob = dataURItoBlob(img);
            formData.append('images', blob, `face_${index}.jpg`);
        });
        
        // Send request to register endpoint
        const response = await fetch('/api/v1/register', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            statusElement.textContent = `Successfully registered ${name}!`;
            statusElement.style.color = 'green';
            
            // Reset form
            document.getElementById('name').value = '';
            document.getElementById('email').value = '';
            capturedImages = [];
            document.getElementById('preview').innerHTML = '';
            document.getElementById('registerBtn').disabled = true;
            
        } else {
            statusElement.textContent = `Error: ${result.detail || 'Unknown error'}`;
            statusElement.style.color = 'red';
        }
        
    } catch (error) {
        console.error('Registration error:', error);
        statusElement.textContent = 'Error registering person. Please try again.';
        statusElement.style.color = 'red';
    }
}

// Recognize a face
async function recognizeFace() {
    const canvas = document.getElementById('canvas2');
    const ctx = canvas.getContext('2d');
    const video = document.getElementById('video2');
    const resultText = document.getElementById('resultText');
    const personInfo = document.getElementById('personInfo');
    
    try {
        // Set canvas dimensions to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Draw current video frame to canvas with better quality
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        resultText.textContent = 'Processing image...';
        resultText.className = 'alert alert-warning';
        personInfo.style.display = 'none';
        
        // Convert canvas to blob with higher quality (95%)
        const blob = await new Promise(resolve => {
            canvas.toBlob(
                blob => resolve(blob),
                'image/jpeg',
                0.95  // 95% quality
            );
        });
        
        if (!blob) {
            throw new Error('Failed to capture image');
        }
        
        console.log('Sending image for recognition:', {
            size: blob.size,
            type: blob.type,
            dimensions: { width: canvas.width, height: canvas.height }
        });
        
        // Create form data and append the blob
        const formData = new FormData();
        formData.append('image', blob, 'face.jpg');
        
        // Show recognizing message
        resultText.textContent = 'Recognizing...';
        
        // Send request to recognize endpoint
        const response = await fetch('/api/v1/recognize', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log('Recognition result:', result);
        
        if (response.ok) {
            if (result.status === 'success') {
                if (result.recognized && result.person) {
                    // Successful recognition with a match
                    resultText.textContent = 'Match found!';
                    resultText.className = 'alert alert-success';
                    
                    // Display person info
                    document.getElementById('personName').textContent = result.person.name;
                    document.getElementById('personEmail').textContent = result.person.email || 'N/A';
                    document.getElementById('confidence').textContent = (result.person.confidence * 100).toFixed(2) + '%';
                    personInfo.style.display = 'block';
                } else {
                    // No match found or not recognized
                    resultText.textContent = result.message || 'No match found. Would you like to register this person?';
                    resultText.className = 'alert alert-info';
                    personInfo.style.display = 'none';
                }
            } else if (result.status === 'no_face') {
                resultText.textContent = 'No face detected in the image. Please try again with a clearer image.';
                resultText.className = 'alert alert-warning';
                personInfo.style.display = 'none';
            } else {
                // Other error cases
                const errorMsg = result.message || 'Unexpected response from server';
                console.error('Recognition API error:', errorMsg);
                resultText.textContent = `Error: ${errorMsg}`;
                resultText.className = 'alert alert-danger';
                personInfo.style.display = 'none';
            }
        } else {
            const errorMsg = result.detail || result.message || 'Unknown error';
            console.error('Recognition API error:', errorMsg);
            resultText.textContent = `Error: ${errorMsg}`;
            resultText.className = 'alert alert-danger';
            personInfo.style.display = 'none';
        }
        
    } catch (error) {
        console.error('Recognition error:', error);
        resultText.textContent = `Error: ${error.message || 'Failed to recognize face. Please try again.'}`;
        resultText.className = 'alert alert-danger';
        personInfo.style.display = 'none';
    }
}

// Helper function to convert base64 to blob
function dataURItoBlob(dataURI) {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    
    return new Blob([ab], { type: mimeString });
}
