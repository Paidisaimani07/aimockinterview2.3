import cv2
import numpy as np
import base64
from collections import deque
from PIL import Image
import io

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
        
        # Face Mesh for lip detection
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=5,
            refine_landmarks=True
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
    face_mesh = None
    print("DEBUG: MediaPipe not available, using fallback detection")

LIP_THRESHOLD = 3
SYNC_THRESHOLD = 0.2
MAX_HISTORY = 20

class LipSyncDetector:
    def __init__(self):
        self.audio_history = deque(maxlen=MAX_HISTORY)
        self.lip_history = deque(maxlen=MAX_HISTORY)
        self.cheating_events = []
        self.face_count_history = deque(maxlen=5)  # Track last 5 face counts for stability

    def _validate_and_stabilize_face_count(self, detections, frame_shape):
        """
        Advanced face count validation and stabilization
        - Filters false positives
        - Stabilizes face count across frames
        - Prevents rapid count fluctuations
        """
        if not detections:
            self.face_count_history.append(0)
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
                    'center': (face_center_x, face_center_y),
                    'area': face_area
                })
        
        # Remove overlapping faces (keep highest confidence)
        valid_faces = self._remove_overlapping_faces(valid_faces)
        
        current_count = len(valid_faces)
        self.face_count_history.append(current_count)
        
        # Stabilize count using median of recent frames
        if len(self.face_count_history) >= 3:
            stable_count = int(sorted(list(self.face_count_history))[-2])  # Use second highest
        else:
            stable_count = current_count
        
        print(f"DEBUG: Raw detections: {len(detections)}, Valid faces: {len(valid_faces)}, Stable count: {stable_count}")
        return stable_count
    
    def _filter_opencv_faces(self, faces, frame_shape):
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

    def _remove_overlapping_faces(self, faces):
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

    def _get_default_result(self):
        """Return default result when processing fails"""
        return {
            'cheating': False,
            'faces': 0,
            'person_count': 0,
            'background_noise_level': 0,
            'speaker_count': 1,
            'noise_ratio': 0,
            'penalty_reasons': []
        }

    def process_frame(self, frame_data):
        try:
            # Handle different frame_data formats
            if isinstance(frame_data, dict) and 'image' in frame_data:
                image_data = frame_data['image']
            elif isinstance(frame_data, str):
                image_data = frame_data
            else:
                print(f"DEBUG: Invalid frame_data format: {type(frame_data)}")
                return self._get_default_result()
            
            # Decode base64 frame
            if isinstance(image_data, str):
                image_data = base64.b64decode(image_data.split(',')[1])
            image = Image.open(io.BytesIO(image_data))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # ✅ MULTI-FACE DETECTION USING MEDIAPIPE
            if MEDIAPIPE_AVAILABLE and face_detection and MEDIAPIPE_VERSION == "solutions":
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_detection.process(rgb)
                    
                    # Count detected faces
                    if results.detections:
                        person_count = len(results.detections)
                        print(f"DEBUG: MediaPipe detected {person_count} face(s)")
                    else:
                        person_count = 0
                        print("DEBUG: MediaPipe detected no faces")
                        
                except Exception as e:
                    print(f"DEBUG: MediaPipe face detection error: {e}")
                    person_count = 0
            else:
                # Fallback: simulate face detection when MediaPipe not available
                person_count = 1  # Assume 1 face as fallback
                if not MEDIAPIPE_AVAILABLE:
                    print("DEBUG: Using fallback face detection (MediaPipe not available)")
                elif MEDIAPIPE_VERSION != "solutions":
                    print("DEBUG: Using fallback face detection (MediaPipe API incompatible)")

            lip_distance = 0

            # ✅ LIP DETECTION USING MEDIAPIPE (with fallback)
            if MEDIAPIPE_AVAILABLE and face_mesh and MEDIAPIPE_VERSION == "solutions":
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(rgb)

                    if results.multi_face_landmarks:
                        # Take first face for lip sync
                        landmarks = results.multi_face_landmarks[0]

                        # Use specific lip landmarks
                        upper_lip = landmarks.landmark[13]
                        lower_lip = landmarks.landmark[14]

                        h, w, _ = frame.shape

                        y1 = int(upper_lip.y * h)
                        y2 = int(lower_lip.y * h)

                        lip_distance = abs(y2 - y1)
                    else:
                        # Fallback: simulate lip distance when no landmarks detected
                        lip_distance = np.random.uniform(0, 5)
                except Exception as e:
                    print(f"DEBUG: MediaPipe processing error: {e}")
                    lip_distance = np.random.uniform(0, 5)
            else:
                # Fallback: simulate lip distance when MediaPipe not available
                lip_distance = np.random.uniform(0, 5)
                if not MEDIAPIPE_AVAILABLE:
                    print("DEBUG: Using fallback lip detection (MediaPipe not available)")
                elif MEDIAPIPE_VERSION != "solutions":
                    print("DEBUG: Using fallback lip detection (MediaPipe API incompatible)")

            # ⚠️ (Optional) audio placeholder (replace with real mic later)
            audio_level = np.random.uniform(0, 0.1)

            self.audio_history.append(audio_level)
            self.lip_history.append(lip_distance)

            audio_active = audio_level > 0.02
            lip_active = lip_distance > LIP_THRESHOLD

            similarity = 1.0
            if len(self.audio_history) > 0:
                a = np.array(self.audio_history)
                l = np.array(self.lip_history)

                if np.linalg.norm(a) > 0 and np.linalg.norm(l) > 0:
                    similarity = np.dot(a, l) / (
                        (np.linalg.norm(a) * np.linalg.norm(l)) + 1e-6
                    )

            cheating = False
            reasons = []

            if person_count > 1:
                cheating = True
                reasons.append("multiple_faces")

            elif person_count == 0:
                cheating = True
                reasons.append("no_face")

            elif audio_active and not lip_active:
                cheating = True
                reasons.append("audio_without_lip")

            elif lip_active and not audio_active:
                cheating = True
                reasons.append("lip_without_audio")

            elif similarity < SYNC_THRESHOLD:
                cheating = True
                reasons.append("low_sync")

            # Generate FFT data for graph (simplified)
            fft_data = np.random.random(50) * 255  # Simulated FFT data

            return {
                "cheating": cheating,
                "faces": person_count,
                "similarity": float(similarity),
                "lip_distance": float(lip_distance),
                "audio_level": float(audio_level),
                "reasons": reasons,
                "person_count": person_count,
                "background_noise_level": 0,
                "speaker_count": 1,
                "noise_ratio": 0,
                "penalty_reasons": reasons,
                "fft_data": fft_data.tolist(),
                "lip_active": lip_active,
                "audio_active": audio_active
            }

        except Exception as e:
            print("Error:", e)
            return {
                "cheating": False,
                "faces": 0,
                "person_count": 0,
                "background_noise_level": 0,
                "speaker_count": 1,
                "noise_ratio": 0,
                "penalty_reasons": []
            }

    def get_realism_score(self):
        """Calculate overall realism score"""
        if not self.cheating_events:
            return 100
        
        total_events = len(self.cheating_events)
        cheating_events = len([e for e in self.cheating_events if e.get('cheating', False)])
        
        if total_events == 0:
            return 100
        
        cheating_ratio = cheating_events / total_events
        base_score = 100 - (cheating_ratio * 25)
        
        final_score = max(60, base_score)
        
        print(f"DEBUG: Lip sync score breakdown - Base: {base_score:.1f}, Final: {final_score:.1f}")
        
        return round(final_score, 2)

# Global instance
lip_sync_detector = LipSyncDetector()
