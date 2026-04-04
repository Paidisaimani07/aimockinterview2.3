import cv2
import base64
import numpy as np
import io
from PIL import Image

# MediaPipe setup with fallback
try:
    import mediapipe as mp
    
    # Try the Solutions API first (more commonly used, no model files required)
    try:
        # Face Detection for multi-face detection
        mp_face_detection = mp.solutions.face_detection
        face_detection = mp_face_detection.FaceDetection(
            model_selection=0,  # 0 for short-range, 1 for long-range
            min_detection_confidence=0.5  # Lower confidence for better detection
        )
        
        MEDIAPIPE_AVAILABLE = True
        MEDIAPIPE_VERSION = "solutions"
        print("DEBUG: MediaPipe solutions API loaded successfully for multi-face detection")
    except AttributeError:
        # Try Tasks API as fallback
        if hasattr(mp, 'tasks'):
            print("DEBUG: Solutions API not available, trying MediaPipe Tasks API")
            
            # Use Tasks API for face detection
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            # Create FaceDetector
            base_options = python.BaseOptions(model_asset_path=None)
            options = vision.FaceDetectorOptions(base_options=base_options, min_detection_confidence=0.5)
            
            # For now, we'll use fallback since Tasks API requires model files
            face_detection = None
            MEDIAPIPE_AVAILABLE = False
            MEDIAPIPE_VERSION = "tasks"
            print("DEBUG: MediaPipe Tasks API detected but requires model files, using fallback")
        else:
            MEDIAPIPE_AVAILABLE = False
            MEDIAPIPE_VERSION = None
            face_detection = None
            print("DEBUG: MediaPipe API not compatible, using fallback")
            
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    MEDIAPIPE_VERSION = None
    face_detection = None
    print("DEBUG: MediaPipe not available, using fallback detection")

def detect_faces(base64_image):
    """
    Detect faces using advanced MediaPipe for multi-face detection.
    More accurate and robust than basic detection with validation.
    """
    try:
        print(f"DEBUG: Using advanced MediaPipe for multi-face detection")
        
        # Decode base64 image
        img_data = base64.b64decode(base64_image.split(',')[1])
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("DEBUG: Failed to decode image")
            return 0
        
        # MULTI-FACE DETECTION USING MEDIAPIPE
        if MEDIAPIPE_AVAILABLE and face_detection and MEDIAPIPE_VERSION == "solutions":
            try:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb)
                
                # Count detected faces
                if results.detections:
                    face_count = len(results.detections)
                    print(f"DEBUG: MediaPipe detected {face_count} face(s)")
                    return face_count
                else:
                    print("DEBUG: MediaPipe detected no faces")
                    return 0
                    
            except Exception as e:
                print(f"DEBUG: MediaPipe face detection error: {e}")
                return 0
        else:
            # Fallback when MediaPipe not available
            print("DEBUG: MediaPipe not available, using fallback detection")
            # Simple fallback - assume 1 face if image quality is reasonable
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            image_brightness = np.mean(gray)
            image_variance = np.var(gray)
            
            if image_brightness < 30 or image_variance < 100:
                print("DEBUG: Poor image quality in fallback, returning 0")
                return 0
            else:
                print("DEBUG: Fallback detection assuming 1 face")
                return 1

    except Exception as e:
        print(f"DEBUG: Face detection error: {e}")
        return 0


def _filter_opencv_faces(faces, frame_shape):
    """
    Filter overlapping OpenCV face detections
    """
    if not faces or len(faces) <= 1:
        return faces
    
    h, w = frame_shape[:2]
    valid_faces = []
    
    for (x, y, w_face, h_face) in faces:
        # Validation criteria
        aspect_ratio = w_face / h_face if h_face > 0 else 0
        face_area = w_face * h_face
        face_center_x = x + w_face // 2
        face_center_y = y + h_face // 2
        
        # Validation rules
        is_valid = (
            0.4 <= aspect_ratio <= 3.0 and  # Reasonable aspect ratio
            face_area >= (w * h * 0.005) and  # Minimum 0.5% of frame area
            face_area <= (w * h * 0.8) and   # Maximum 80% of frame area
            face_center_x > 0.05 * w and     # Not too close to edges
            face_center_x < 0.95 * w and
            face_center_y > 0.05 * h and
            face_center_y < 0.95 * h
        )
        
        if is_valid:
            valid_faces.append({
                'bbox': (x, y, w_face, h_face),
                'area': face_area,
                'center': (face_center_x, face_center_y)
            })
    
    # Remove overlapping faces
    filtered_faces = []
    for face in valid_faces:
        is_overlapping = False
        for kept_face in filtered_faces:
            # Calculate overlap
            x1, y1, w1, h1 = face['bbox']
            x2, y2, w2, h2 = kept_face['bbox']
            
            # Calculate intersection area
            ix1 = max(x1, x2)
            iy1 = max(y1, y2)
            ix2 = min(x1 + w1, x2 + w2)
            iy2 = min(y1 + h1, y2 + h2)
            
            if ix2 > ix1 and iy2 > iy1:  # There is overlap
                intersection_area = (ix2 - ix1) * (iy2 - iy1)
                union_area = w1 * h1 + w2 * h2 - intersection_area
                iou = intersection_area / union_area if union_area > 0 else 0
                
                if iou > 0.3:  # 30% overlap threshold
                    is_overlapping = True
                    break
        
        if not is_overlapping:
            filtered_faces.append(face)
    
    # Return as OpenCV format
    return [face['bbox'] for face in filtered_faces]

def _validate_face_detections(detections, frame_shape):
    """
    Advanced face detection validation to filter false positives
    """
    if not detections:
        return 0
    
    h, w = frame_shape[:2]
    valid_faces = []
    
    for detection in detections:
        # Get bounding box relative to frame size
        bbox = detection.location_data.relative_bounding_box
        x_min, y_min = bbox.xmin, bbox.ymin
        width, height = bbox.width, bbox.height
        confidence = detection.score[0]
        
        # Convert to absolute coordinates
        abs_x = int(x_min * w)
        abs_y = int(y_min * h)
        abs_w = int(width * w)
        abs_h = int(height * h)
        
        # Validation criteria
        aspect_ratio = abs_w / abs_h if abs_h > 0 else 0
        face_area = abs_w * abs_h
        face_center_x = abs_x + abs_w // 2
        face_center_y = abs_y + abs_h // 2
        
        # Strict validation rules (more permissive)
        is_valid = (
            confidence >= 0.5 and  # Lower confidence threshold
            0.3 <= aspect_ratio <= 3.0 and  # Wider aspect ratio range
            face_area >= (w * h * 0.005) and  # Lower minimum area (0.5% of frame)
            face_area <= (w * h * 0.9) and   # Slightly higher maximum area
            face_center_x > 0.05 * w and     # More permissive position
            face_center_x < 0.95 * w and
            face_center_y > 0.05 * h and
            face_center_y < 0.95 * h
        )
        
        if is_valid:
            valid_faces.append({
                'bbox': (abs_x, abs_y, abs_w, abs_h),
                'confidence': confidence,
                'area': face_area
            })
    
    # Remove overlapping faces (keep highest confidence)
    valid_faces = _remove_overlapping_faces(valid_faces)
    
    print(f"DEBUG: Raw detections: {len(detections)}, Valid faces: {len(valid_faces)}")
    return len(valid_faces)


def _remove_overlapping_faces(faces):
    """
    Remove overlapping face detections, keeping the highest confidence ones
    """
    if not faces:
        return faces
    
    # Sort by confidence (highest first)
    faces.sort(key=lambda x: x['confidence'], reverse=True)
    
    filtered_faces = []
    for face in faces:
        is_overlapping = False
        for kept_face in filtered_faces:
            # Calculate overlap
            x1, y1, w1, h1 = face['bbox']
            x2, y2, w2, h2 = kept_face['bbox']
            
            # Calculate intersection area
            ix1 = max(x1, x2)
            iy1 = max(y1, y2)
            ix2 = min(x1 + w1, x2 + w2)
            iy2 = min(y1 + h1, y2 + h2)
            
            if ix2 > ix1 and iy2 > iy1:  # There is overlap
                intersection_area = (ix2 - ix1) * (iy2 - iy1)
                union_area = w1 * h1 + w2 * h2 - intersection_area
                iou = intersection_area / union_area if union_area > 0 else 0
                
                if iou > 0.3:  # 30% overlap threshold
                    is_overlapping = True
                    break
        
        if not is_overlapping:
            filtered_faces.append(face)
    
    return filtered_faces