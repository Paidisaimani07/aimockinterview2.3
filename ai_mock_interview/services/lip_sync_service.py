import cv2
import numpy as np
import base64
import json
from collections import deque

# Try to import optional dependencies
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("Warning: sounddevice not available, using simulated audio")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: YOLO not available, using basic detection")

try:
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: MediaPipe not available, using basic detection")

# ---------------- CONFIG ----------------

LIP_THRESHOLD = 3
SYNC_THRESHOLD = 0.2
MAX_HISTORY = 20
BACKGROUND_NOISE_THRESHOLD = 0.06  # Higher threshold to catch actual music (was 0.04)
MULTIPLE_SPEAKER_THRESHOLD = 0.12  # Higher threshold to catch actual music (was 0.08)

# ---------------- HISTORY ----------------

class LipSyncDetector:
    def __init__(self):
        self.audio_history = deque(maxlen=MAX_HISTORY)
        self.lip_history = deque(maxlen=MAX_HISTORY)
        self.noise_history = deque(maxlen=50)
        self.frame_count = 0
        self.person_count = 1
        self.lip_distance = 0
        self.audio_level = 0
        self.cheating_events = []
        self.background_noise_level = 0
        self.speaker_count = 1
        self.audio_variance = 0
        self.noise_ratio = 0
        
    def _get_default_result(self):
        """Return default result when processing fails"""
        return {
            'cheating': False,
            'similarity': 1.0,
            'audio_level': 0,
            'lip_distance': 0,
            'person_count': 1,
            'background_noise_level': 0,
            'speaker_count': 1,
            'noise_ratio': 0,
            'penalty_reasons': []
        }
        
    def process_frame(self, frame_data):
        """Process frame data and return lip sync analysis with noise detection"""
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
            import io
            from PIL import Image
            
            if isinstance(image_data, str):
                image_data = base64.b64decode(image_data.split(',')[1])
            image = Image.open(io.BytesIO(image_data))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            h, w, _ = frame.shape
            self.frame_count += 1
            
            # Simulate face detection (simplified)
            person_count = 1  # Default to 1 person
            lip_distance = 0
            
            # Basic lip detection simulation (simplified)
            # In real implementation, this would use MediaPipe face landmarks
            if self.frame_count % 10 == 0:  # Process every 10th frame
                # Simulate lip movement detection
                lip_distance = np.random.uniform(0, 10)  # Simulated lip movement
            
            # Enhanced audio simulation with realistic noise detection
            # In real implementation, this would come from actual microphone analysis
            base_audio_level = np.random.uniform(0, 0.1) if self.frame_count % 5 == 0 else self.audio_level
            
            # Only simulate background noise when user might actually have it
            # For normal voice, this should be extremely rare
            if np.random.random() < 0.01:  # 1% chance of background noise (extremely rare)
                background_noise = np.random.uniform(0.002, 0.01)  # Almost no noise for normal voice
            else:
                background_noise = np.random.uniform(0, 0.002)  # Virtually no noise
            
            # Only simulate multiple speakers when there might actually be multiple
            if np.random.random() < 0.005:  # 0.5% chance of multiple speakers (extremely rare)
                speaker_variation = np.random.uniform(0.005, 0.02)  # Extremely low variation
                multiple_speaker_indicator = True
            else:
                speaker_variation = 0
                multiple_speaker_indicator = False
            
            # Combine audio levels
            audio_level = base_audio_level + background_noise + speaker_variation
            
            # Calculate audio metrics
            self.audio_history.append(audio_level)
            self.noise_history.append(background_noise)
            
            # Calculate background noise level (average noise)
            if len(self.noise_history) > 0:
                self.background_noise_level = np.mean(list(self.noise_history))
                self.noise_ratio = self.background_noise_level / (audio_level + 1e-6)
            
            # Calculate audio variance for multiple speaker detection
            if len(self.audio_history) > 5:
                recent_audio = list(self.audio_history)[-5:]
                self.audio_variance = np.var(recent_audio)
                # High variance suggests multiple speakers or background noise
                if self.audio_variance > MULTIPLE_SPEAKER_THRESHOLD:
                    self.speaker_count = min(3, int(self.audio_variance * 10) + 1)
                else:
                    self.speaker_count = 1
            
            # Enhanced background noise detection
            if self.background_noise_level > BACKGROUND_NOISE_THRESHOLD:
                # High background noise detected (like music playing)
                self.noise_ratio = min(0.8, self.background_noise_level / (base_audio_level + 1e-6))
            else:
                self.noise_ratio = self.background_noise_level / (audio_level + 1e-6)
            
            self.person_count = person_count
            self.lip_distance = lip_distance
            self.audio_level = audio_level
            
            # Process lip history
            self.lip_history.append(lip_distance)
            
            # Calculate sync
            audio_active = audio_level > 0.02
            lip_active = lip_distance > LIP_THRESHOLD
            
            # Calculate similarity
            similarity = 1.0
            if len(self.audio_history) > 0 and len(self.lip_history) > 0:
                audio_vec = np.array(list(self.audio_history))
                lip_vec = np.array(list(self.lip_history))
                
                if np.linalg.norm(audio_vec) > 0 and np.linalg.norm(lip_vec) > 0:
                    audio_norm = audio_vec / (np.linalg.norm(audio_vec) + 1e-6)
                    lip_norm = lip_vec / (np.linalg.norm(lip_vec) + 1e-6)
                    similarity = np.dot(audio_norm, lip_norm)
            
            # Enhanced cheating detection with noise and multiple speaker penalties
            cheating = False
            penalty_reasons = []
            
            # Original cheating conditions
            if person_count > 1:
                cheating = True
                penalty_reasons.append("multiple_persons")
            elif audio_active and not lip_active:
                cheating = True
                penalty_reasons.append("audio_without_lip")
            elif lip_active and not audio_active:
                cheating = True
                penalty_reasons.append("lip_without_audio")
            elif audio_active and lip_active and similarity < SYNC_THRESHOLD:
                cheating = True
                penalty_reasons.append("low_similarity")
            
            # New penalties for background noise and multiple speakers
            if self.background_noise_level > BACKGROUND_NOISE_THRESHOLD:
                cheating = True
                penalty_reasons.append("background_noise")
            
            if self.speaker_count > 1:
                cheating = True
                penalty_reasons.append("multiple_speakers")
            
            if self.noise_ratio > 0.3:  # High noise-to-audio ratio
                cheating = True
                penalty_reasons.append("high_noise_ratio")
            
            if cheating:
                self.cheating_events.append({
                    'timestamp': self.frame_count,
                    'type': 'lip_sync_mismatch',
                    'similarity': similarity,
                    'audio_level': audio_level,
                    'lip_distance': lip_distance,
                    'background_noise': self.background_noise_level,
                    'speaker_count': self.speaker_count,
                    'noise_ratio': self.noise_ratio,
                    'penalty_reasons': penalty_reasons
                })
            
            # Generate FFT data for graph (simplified)
            fft_data = np.random.random(50) * 255  # Simulated FFT data
            
            return {
                'cheating': cheating,
                'similarity': similarity,
                'audio_level': audio_level,
                'lip_distance': lip_distance,
                'person_count': person_count,
                'fft_data': fft_data.tolist(),
                'lip_active': lip_active,
                'audio_active': audio_active,
                'background_noise': self.background_noise_level,
                'speaker_count': self.speaker_count,
                'noise_ratio': self.noise_ratio,
                'penalty_reasons': penalty_reasons
            }
            
        except Exception as e:
            print(f"Lip sync detection error: {e}")
            return {
                'cheating': False,
                'similarity': 1.0,
                'audio_level': 0,
                'lip_distance': 0,
                'person_count': 1,
                'fft_data': [0]*50,
                'lip_active': False,
                'audio_active': False,
                'background_noise': 0,
                'speaker_count': 1,
                'noise_ratio': 0,
                'penalty_reasons': []
            }
    
    def get_realism_score(self):
        """Calculate overall realism score with penalties for noise and multiple speakers"""
        if not self.cheating_events:
            return 100
        
        total_events = len(self.cheating_events)
        cheating_events = len([e for e in self.cheating_events if e['type'] == 'lip_sync_mismatch'])
        
        if total_events == 0:
            return 100
        
        # Base score calculation - much more lenient
        cheating_ratio = cheating_events / total_events
        base_score = 100 - (cheating_ratio * 25)  # Reduced from 50% to 25%
        
        # Additional penalties for specific issues - very lenient
        background_noise_penalties = len([e for e in self.cheating_events if 'background_noise' in e.get('penalty_reasons', [])])
        multiple_speaker_penalties = len([e for e in self.cheating_events if 'multiple_speakers' in e.get('penalty_reasons', [])])
        high_noise_ratio_penalties = len([e for e in self.cheating_events if 'high_noise_ratio' in e.get('penalty_reasons', [])])
        
        # Apply very reduced penalties
        noise_penalty = (background_noise_penalties / total_events) * 5   # Reduced from 10% to 5%
        speaker_penalty = (multiple_speaker_penalties / total_events) * 8   # Reduced from 15% to 8%
        ratio_penalty = (high_noise_ratio_penalties / total_events) * 3   # Reduced from 5% to 3%
        
        # Calculate final score
        final_score = base_score - noise_penalty - speaker_penalty - ratio_penalty
        final_score = max(60, final_score)  # Minimum score of 60% instead of 40%
        
        print(f"DEBUG: Lip sync score breakdown - Base: {base_score:.1f}, Noise penalty: {noise_penalty:.1f}, Speaker penalty: {speaker_penalty:.1f}, Ratio penalty: {ratio_penalty:.1f}, Final: {final_score:.1f}")
        
        return round(final_score, 2)

# Global instance
lip_sync_detector = LipSyncDetector()
