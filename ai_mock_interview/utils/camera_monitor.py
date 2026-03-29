import cv2
import base64
import numpy as np
import io
from PIL import Image

def detect_faces(base64_image):
    """
    Detect faces with strict criteria - only return 0 if no face or camera is blocked.
    More lenient to avoid false violations when face is clearly visible.
    """
    try:
        print(f"DEBUG: Using enhanced OpenCV for face detection")
        
        # Decode base64 image
        img_data = base64.b64decode(base64_image.split(',')[1])
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("DEBUG: Failed to decode image")
            return 0
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization for better face detection
        gray = cv2.equalizeHist(gray)
        
        # Load face cascade
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Use more reliable face detection parameters
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
        
        # Very lenient filtering - only remove obvious false positives
        valid_faces = []
        for (x, y, w, h) in faces:
            aspect_ratio = w / h
            face_area = w * h
            
            # Very basic validation - much more lenient
            if (0.6 <= aspect_ratio <= 1.5 and  # Wide aspect ratio range
                w >= 60 and h >= 60 and           # Reasonable minimum size
                face_area >= 3600 and             # Minimum area
                y > 10):                          # Not at very top of image
                valid_faces.append((x, y, w, h))
        
        face_count = len(valid_faces)
        
        # Additional check: if we found some faces but they seem too small, 
        # it might be a partial face or far away - still count as face present
        if face_count == 0 and len(faces) > 0:
            # Check if any detected face has reasonable characteristics
            for (x, y, w, h) in faces:
                if w >= 40 and h >= 40:  # Very minimal size requirement
                    face_count = 1
                    print("DEBUG: Found small face, counting as face present")
                    break
        
        # Final validation: only return 0 if absolutely no face detected
        # and image quality is good enough to detect faces
        if face_count == 0:
            # Check if image is too dark or blurry (might be camera covered)
            image_brightness = np.mean(gray)
            image_variance = np.var(gray)
            
            if image_brightness < 30:  # Very dark - possibly camera covered
                print("DEBUG: Image very dark, camera possibly covered")
                return 0
            elif image_variance < 100:  # Low variance - possibly camera covered with hand
                print("DEBUG: Low image variance, camera possibly covered")
                return 0
            else:
                print("DEBUG: No face detected in clear image")
                return 0
        else:
            print(f"DEBUG: Found {face_count} valid face(s)")
            return face_count

    except Exception as e:
        print(f"DEBUG: Face detection error: {e}")
        return 0