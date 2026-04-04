let currentQuestion = "";
let currentAnswer = "";
let scores = [];

let mediaRecorder;
let audioChunks = [];
let recordingStartTime;
let timerInterval;
let silenceTimer;
let audioContext;
let analyser;
let microphone;
let isRecording = false;

// Interview timer and monitoring variables
let interviewTimer;
let timeRemaining = 1200; // 20 minutes in seconds
let multipleFaceViolations = 0; // Multiple faces detected
let noFaceViolations = 0; // No face detected/camera hidden
let tabViolations = 0; // Tab switch violations
let interviewActive = false;

// ---------------- INTERVIEW TIMER ----------------
function startInterviewTimer() {
    console.log("Starting interview timer...");
    interviewActive = true;
    updateTimerDisplay();
    
    interviewTimer = setInterval(() => {
        timeRemaining--;
        console.log("Time remaining:", timeRemaining);
        updateTimerDisplay();
        
        if (timeRemaining <= 0) {
            endInterviewDueToTimeout();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        timerElement.textContent = display;
        console.log("Timer updated:", display);
    } else {
        console.log("Timer element not found!");
    }
    
    // Change color when time is running out
    if (timeRemaining <= 300) { // 5 minutes left
        timerElement.style.color = '#e74c3c';
    } else if (timeRemaining <= 600) { // 10 minutes left
        timerElement.style.color = '#f39c12';
    }
}

function stopInterviewTimer() {
    interviewActive = false;
    if (interviewTimer) {
        clearInterval(interviewTimer);
        interviewTimer = null;
    }
}

// ---------------- SCREENSHOT CAPTURE ----------------
function captureScreenshot() {
    return new Promise((resolve) => {
        // Capture current tab (interview page) as evidence of when the violation occurred
        html2canvas(document.body).then(canvas => {
            const screenshot = canvas.toDataURL('image/png');
            resolve(screenshot);
        }).catch(err => {
            console.error('Error capturing screenshot:', err);
            resolve(null);
        });
    });
}

// Add html2canvas library dynamically
function loadHtml2Canvas() {
    if (typeof html2canvas === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
        document.head.appendChild(script);
    }
}

// Load html2canvas when page loads
document.addEventListener('DOMContentLoaded', loadHtml2Canvas);

// ---------------- VIOLATION VISUAL FEEDBACK ----------------
function showViolationAlert(type, message) {
    // Add red border to video element instead of covering entire screen
    const videoElement = document.querySelector('video');
    if (videoElement) {
        videoElement.style.border = '8px solid #ff0000';
        videoElement.style.boxSizing = 'border-box';
        videoElement.style.transition = 'border-color 0.3s ease';
    }
    
    // Create small violation alert (not full screen)
    const alertOverlay = document.createElement('div');
    alertOverlay.id = 'violationAlert';
    alertOverlay.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(255, 0, 0, 0.95);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 10000;
        font-family: Arial, sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        max-width: 300px;
        animation: slideIn 0.3s ease-out;
    `;
    
    const icon = type === 'face' ? '👤' : '🔄';
    alertOverlay.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 24px;">${icon}</div>
            <div>
                <div style="font-weight: bold; font-size: 14px; margin-bottom: 2px;">VIOLATION DETECTED!</div>
                <div style="font-size: 12px; opacity: 0.9;">${message}</div>
            </div>
        </div>
    `;
    
    // Add slide-in animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(alertOverlay);
    
    // Remove after 2 seconds
    setTimeout(() => {
        if (videoElement) {
            videoElement.style.border = '';
            videoElement.style.transition = '';
        }
        if (alertOverlay.parentNode) {
            alertOverlay.remove();
        }
        if (style.parentNode) {
            style.remove();
        }
    }, 2000);
}

// ---------------- TAB SWITCHING DETECTION ----------------
let isProcessingViolation = false;

function detectTabSwitch() {
    // Track when user leaves the page
    document.addEventListener('visibilitychange', function() {
        if (document.hidden && interviewActive && !isProcessingViolation) {
            isProcessingViolation = true;
            
            console.log("DEBUG: Visibility change detected - tab switched");
            
            // User switched tabs - capture comprehensive evidence
            const violationData = {
                type: 'tab',
                timestamp: new Date().toISOString(),
                url: window.location.href,
                title: document.title,
                userAgent: navigator.userAgent,
                violationTime: new Date().toLocaleString(),
                detectionMethod: 'visibility_change',
                currentQuestion: currentQuestion || 'No active question',
                interviewProgress: {
                    timeRemaining: timeRemaining,
                    faceViolations: faceViolations,
                    tabViolations: tabViolations
                },
                systemInfo: {
                    platform: navigator.platform,
                    language: navigator.language,
                    screenResolution: `${screen.width}x${screen.height}`,
                    colorDepth: screen.colorDepth,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
                },
                // Enhanced tab detection info
                tabDetection: {
                    pageHidden: document.hidden,
                    visibilityState: document.visibilityState,
                    windowFocused: document.hasFocus(),
                    activeElement: document.activeElement ? document.activeElement.tagName : 'None',
                    referrer: document.referrer,
                    previousUrls: getTabHistory()
                }
            };
            
            // Show visual alert
            showViolationAlert('tab', 'Tab Switch Detected! Interview integrity compromised.');
            
            // Capture current state as evidence
            captureScreenshot().then(screenshot => {
                recordTabViolationWithEvidence(violationData, screenshot);
            });
            
            // Reset processing flag after debounce time
            setTimeout(() => {
                isProcessingViolation = false;
            }, VIOLATION_DEBOUNCE_TIME);
        }
    });
    
    // Track window focus/blur (but don't duplicate with visibility change)
    window.addEventListener('blur', function() {
        if (interviewActive && !isProcessingViolation && !document.hidden) {
            isProcessingViolation = true;
            
            console.log("DEBUG: Window blur detected - potential tab switch");
            
            const violationData = {
                type: 'tab',
                timestamp: new Date().toISOString(),
                url: window.location.href,
                title: document.title,
                userAgent: navigator.userAgent,
                violationTime: new Date().toLocaleString(),
                detectionMethod: 'window_blur',
                currentQuestion: currentQuestion || 'No active question',
                interviewProgress: {
                    timeRemaining: timeRemaining,
                    faceViolations: faceViolations,
                    tabViolations: tabViolations
                },
                systemInfo: {
                    platform: navigator.platform,
                    language: navigator.language,
                    screenResolution: `${screen.width}x${screen.height}`,
                    colorDepth: screen.colorDepth,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
                },
                tabDetection: {
                    pageHidden: document.hidden,
                    visibilityState: document.visibilityState,
                    windowFocused: document.hasFocus(),
                    activeElement: document.activeElement ? document.activeElement.tagName : 'None',
                    referrer: document.referrer,
                    previousUrls: getTabHistory()
                }
            };
            
            // Show visual alert
            showViolationAlert('tab', 'Window Focus Lost! Tab switch detected.');
            
            captureScreenshot().then(screenshot => {
                recordTabViolationWithEvidence(violationData, screenshot);
            });
            
            // Reset processing flag after debounce time
            setTimeout(() => {
                isProcessingViolation = false;
            }, VIOLATION_DEBOUNCE_TIME);
        }
    });
    
    // Track mouse leaving window (might indicate tab switch)
    document.addEventListener('mouseout', function(e) {
        if (e.relatedTarget === null && interviewActive && !isProcessingViolation) {
            // Mouse left the window entirely - log but don't count as violation
            const violationData = {
                type: 'potential_tab_switch',
                timestamp: new Date().toISOString(),
                url: window.location.href,
                title: document.title,
                violationTime: new Date().toLocaleString(),
                detectionMethod: 'mouse_leave_window',
                currentQuestion: currentQuestion || 'No active question',
                interviewProgress: {
                    timeRemaining: timeRemaining,
                    faceViolations: faceViolations,
                    tabViolations: tabViolations
                },
                tabDetection: {
                    pageHidden: document.hidden,
                    visibilityState: document.visibilityState,
                    windowFocused: document.hasFocus(),
                    activeElement: document.activeElement ? document.activeElement.tagName : 'None',
                    mousePosition: `${e.clientX}, ${e.clientY}`,
                    referrer: document.referrer
                }
            };
            
            console.log("Mouse left window - potential tab switch detected");
            console.log("DEBUG: This is logged but not counted as violation");
        }
    });
    
    // Prevent alt+tab
    document.addEventListener('keydown', function(e) {
        if (e.altKey && e.key === 'Tab') {
            e.preventDefault();
            if (interviewActive && !isProcessingViolation) {
                isProcessingViolation = true;
                
                console.log("DEBUG: Alt+Tab attempt blocked");
                
                const violationData = {
                    type: 'tab',
                    timestamp: new Date().toISOString(),
                    url: window.location.href,
                    title: document.title,
                    userAgent: navigator.userAgent,
                    violationTime: new Date().toLocaleString(),
                    detectionMethod: 'alt_tab_blocked',
                    currentQuestion: currentQuestion || 'No active question',
                    interviewProgress: {
                        timeRemaining: timeRemaining,
                        faceViolations: faceViolations,
                        tabViolations: tabViolations
                    },
                    systemInfo: {
                        platform: navigator.platform,
                        language: navigator.language,
                        screenResolution: `${screen.width}x${screen.height}`,
                        colorDepth: screen.colorDepth,
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
                    },
                    tabDetection: {
                        pageHidden: document.hidden,
                        visibilityState: document.visibilityState,
                        windowFocused: document.hasFocus(),
                        activeElement: document.activeElement ? document.activeElement.tagName : 'None',
                        keyCombination: 'Alt+Tab',
                        referrer: document.referrer,
                        previousUrls: getTabHistory()
                    }
                };
                
                // Show visual alert
                showViolationAlert('tab', 'Alt+Tab Attempt Blocked! Tab switch detected.');
                
                captureScreenshot().then(screenshot => {
                    recordTabViolationWithEvidence(violationData, screenshot);
                });
                
                // Reset processing flag after debounce time
                setTimeout(() => {
                    isProcessingViolation = false;
                }, VIOLATION_DEBOUNCE_TIME);
            }
        }
    });
    
    // Track Ctrl+T (new tab) attempts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 't') {
            e.preventDefault();
            if (interviewActive) {
                console.log('Ctrl+T (new tab) attempt blocked');
            }
        }
    });
    
    // Track Ctrl+W (close tab) attempts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'w') {
            e.preventDefault();
            if (interviewActive) {
                console.log('Ctrl+W (close tab) attempt blocked');
            }
        }
    });
}

// Tab history tracking
function getTabHistory() {
    // Try to get recent navigation history (limited by browser security)
    try {
        if (window.performance && window.performance.navigation) {
            return {
                navigationType: window.performance.navigation.type,
                redirectCount: window.performance.navigation.redirectCount
            };
        }
    } catch (e) {
        console.log('Cannot access navigation history');
    }
    return {};
}

// Enhanced tab violation recording with evidence
function recordTabViolationWithEvidence(violationData, screenshot) {
    console.log("DEBUG: Recording tab violation with evidence");
    
    // Call backend with detailed evidence
    fetch('/violation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            type: 'tab',
            screenshot: screenshot,
            evidence: violationData
        })
    })
    .then(res => res.json())
    .then(data => {
        console.log("DEBUG: Tab violation response:", data);
        
        if (data.debounced) {
            console.log("DEBUG: Server-side debounced violation - not counting");
            return; // Don't update UI if debounced
        }
        
        tabViolations = data.tab_violations;
        document.getElementById('tabViolations').textContent = tabViolations;
        showToast('Tab switch detected. Please stay focused on the interview.', 'warning', 3000);
        
        console.log(`DEBUG: Tab violations count: ${tabViolations}, Terminated: ${data.terminated}`);
        
        if (data.terminated) {
            console.log("DEBUG: Interview terminated due to tab violations");
            endInterviewDueToViolation(data.reason);
        }
    })
    .catch(err => console.error('Error recording tab violation:', err));
}

// Initialize tab switching detection
document.addEventListener('DOMContentLoaded', detectTabSwitch);

// ---------------- VIOLATION MONITORING ----------------
let violationDebounceTimer = null;
let lastViolationTime = 0;
const VIOLATION_DEBOUNCE_TIME = 5000; // 5 seconds debounce - very lenient to avoid false violations

function recordMultipleFaceViolation() {
    if (!interviewActive) return;
    
    // Debounce violations
    const now = Date.now();
    if (now - lastViolationTime < VIOLATION_DEBOUNCE_TIME) {
        console.log("DEBUG: Multiple face violation debounced");
        return;
    }
    lastViolationTime = now;
    
    // Show specific visual alert for multiple face violation
    showViolationAlert('face', 'Multiple Faces Detected! More than one person detected.');
    
    // Capture screenshot before sending violation
    captureScreenshot().then(screenshot => {
        // Call backend to record violation with screenshot
        fetch('/violation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                type: 'multiple_faces',
                screenshot: screenshot
            })
        })
        .then(res => res.json())
        .then(data => {
            multipleFaceViolations = data.multiple_face_violations;
            document.getElementById('multipleFaceViolations').textContent = multipleFaceViolations;
            
            // Show toast with violation warning
            let toastMessage = '';
            if (multipleFaceViolations === 1) {
                toastMessage = '⚠️ First Multiple Face Violation! More than one person detected. One more violation will terminate the interview.';
            } else if (multipleFaceViolations >= 2) {
                toastMessage = '❌ Interview Terminated! Multiple face violations detected.';
            }
            
            showToast(toastMessage, 'warning', 3000);
            
            if (data.terminated) {
                endInterviewDueToViolation(data.reason);
            }
        })
        .catch(err => console.error('Error recording multiple face violation:', err));
    });
}

function recordNoFaceViolation() {
    if (!interviewActive) return;
    
    // Debounce violations
    const now = Date.now();
    if (now - lastViolationTime < VIOLATION_DEBOUNCE_TIME) {
        console.log("DEBUG: No face violation debounced");
        return;
    }
    lastViolationTime = now;
    
    // Show specific visual alert for no face violation
    showViolationAlert('face', 'No Face Detected! Camera hidden or covered.');
    
    // Capture screenshot before sending violation
    captureScreenshot().then(screenshot => {
        // Call backend to record violation with screenshot
        fetch('/violation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                type: 'no_face',
                screenshot: screenshot
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.debounced) return;
            
            noFaceViolations = data.no_face_violations;
            
            // Update the counter in the status bar
            const noFaceEl = document.getElementById('noFaceViolations');
            if (noFaceEl) noFaceEl.textContent = noFaceViolations;
            
            // Show the warning banner
            const noFaceWarning = document.getElementById('noFaceWarning');
            const noFaceWarningText = document.getElementById('noFaceWarningText');
            if (noFaceWarning) noFaceWarning.classList.remove('hidden');
            
            // Update warning message based on violation count
            if (noFaceWarningText) {
                if (noFaceViolations === 1) {
                    noFaceWarningText.innerHTML = '⚠️ <strong>First No Face Violation!</strong> Camera not detected or covered. ' + (5 - noFaceViolations) + ' violations remaining before termination.';
                } else if (noFaceViolations < 5) {
                    noFaceWarningText.innerHTML = '⚠️ <strong>No Face Warning ' + noFaceViolations + '/5!</strong> Please keep your face visible. ' + (5 - noFaceViolations) + ' violations remaining.';
                } else {
                    noFaceWarningText.innerHTML = '❌ <strong>Interview Terminated!</strong> Exceeded maximum no-face violations.';
                }
            }
            
            showToast('⚠️ No face detected! Violation ' + noFaceViolations + '/5', 'warning', 3000);
            
            if (data.terminated) {
                endInterviewDueToViolation(data.reason);
            }
        })
        .catch(err => console.error('Error recording no face violation:', err));
    });
    
    // Hide warning banner after 4 seconds
    setTimeout(() => {
        const noFaceWarning = document.getElementById('noFaceWarning');
        if (noFaceWarning) noFaceWarning.classList.add('hidden');
    }, 4000);
}

function recordTabViolation() {
    if (!interviewActive) return;
    
    // Debounce violations
    const now = Date.now();
    if (now - lastViolationTime < VIOLATION_DEBOUNCE_TIME) {
        console.log("DEBUG: Tab violation debounced");
        return;
    }
    lastViolationTime = now;
    
    // Capture screenshot before sending violation
    captureScreenshot().then(screenshot => {
        // Call backend to record violation with screenshot
        fetch('/violation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                type: 'tab',
                screenshot: screenshot
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.debounced) {
                console.log("DEBUG: Server-side debounced violation - not counting");
                return; // Don't update UI if debounced
            }
            
            tabViolations = data.tab_violations;
            document.getElementById('tabViolations').textContent = tabViolations;
            
            // Show toast with violation warning
            let toastMessage = '';
            if (tabViolations === 1) {
                toastMessage = '⚠️ First Tab Switch! Tab switch detected. One more violation will terminate the interview.';
            } else if (tabViolations >= 2) {
                toastMessage = '❌ Interview Terminated! Multiple tab switches detected.';
            }
            
            showToast(toastMessage, 'warning', 3000);
            
            console.log(`DEBUG: Tab violations count: ${tabViolations}, Terminated: ${data.terminated}`);
            
            if (data.terminated) {
                console.log("DEBUG: Interview terminated due to tab violations");
                endInterviewDueToViolation(data.reason);
            }
        })
        .catch(err => console.error('Error recording tab violation:', err));
    });
}

// ---------------- INTERVIEW TERMINATION ----------------
function endInterviewDueToTimeout() {
    stopInterviewTimer();
    if (typeof stopCameraMonitoring === 'function') {
        stopCameraMonitoring();
    }
    showToast('Interview time expired! The interview will now end.', 'info', 2000);
    setTimeout(() => {
        window.location.href = '/result';
    }, 2000);
}

function endInterviewDueToViolation(reason) {
    stopInterviewTimer();
    if (typeof stopCameraMonitoring === 'function') {
        stopCameraMonitoring();
    }
    showToast(`Interview terminated due to: ${reason}`, 'error', 2000);
    setTimeout(() => {
        window.location.href = '/result';
    }, 2000);
}

// Tab switch detection
document.addEventListener('visibilitychange', function() {
    if (document.hidden && interviewActive) {
        recordTabViolation();
    }
});

// Prevent alt+tab
document.addEventListener('keydown', function(e) {
    if (e.altKey && e.key === 'Tab') {
        e.preventDefault();
        if (interviewActive) {
            recordTabViolation();
        }
    }
});

// ---------------- START INTERVIEW ----------------
async function startInterview() {

    const name = document.getElementById("name").value;
    const jd = document.getElementById("jd").value;
    const resumeFile = document.getElementById("resumeFile").files[0];

    // Check file size (5MB limit)
    if (resumeFile && resumeFile.size > 5 * 1024 * 1024) {
        // Change file display to red when showing error toast
        const fileNameDisplay = document.getElementById('fileNameDisplay');
        const fileSizeMB = (resumeFile.size / (1024 * 1024)).toFixed(2);
        fileNameDisplay.className = 'mt-2 text-sm text-red-600 font-500';
        fileNameDisplay.textContent = ' ' + resumeFile.name + ' (' + fileSizeMB + 'MB) - File size exceeds 5MB limit';
        
        showToast('File size limit exceeded! Maximum file size is 5MB', 'error', 3000);
        return;
    }

    if (!jd || !resumeFile) {
        showToast('Please fill all required fields (Name, Job Description, and Resume)', 'error', 3000);
        return;
    }

    const formData = new FormData();
    formData.append("name", name);
    formData.append("jd", jd);
    formData.append("resume", resumeFile);

    // Show loading indicator while starting interview
    document.getElementById("setup").style.display = "none";
    document.getElementById("interview").style.display = "block";
    document.getElementById("question").innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <div class="loading-spinner" style="font-size: 32px;">🔄</div>
            <p style="margin-top: 20px; color: #8b5cf6; font-weight: 600;">Starting Interview...</p>
            <p style="margin-top: 5px; color: #6b7280; font-size: 14px;">Analyzing your resume and generating first question</p>
        </div>
    `;

    const res = await fetch("/start", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    console.log("START RESPONSE:", data);

    if (data.status === "error" || data.status === "rejected") {
        alert(data.message || "Resume validation failed.");
        // Redirect back to instructions page
        window.location.href = "/";
        return;
    }

    if (data.error) {
        alert(data.error);
        return;
    }

    if (!data.question) {
        alert("Server did not return a question");
        return;
    }

    console.log("Interview section displayed, starting timer...");
    
    // Start interview timer
    startInterviewTimer();

    // Initialize camera monitoring when interview starts
    if (typeof initCameraMonitoring === 'function') {
        initCameraMonitoring();
    }

    // Enable tab monitoring after interview starts
    if (typeof enableTabMonitoring === 'function') {
        enableTabMonitoring();
    }

    currentQuestion = data.question;

    document.getElementById("question").innerHTML =
        "<b>AI:</b> " + currentQuestion;
    
    // Display match percentage if available
    if (data.match_percentage) {
        document.getElementById("matchPercentage").textContent = data.match_percentage;
    }
    
    // Speak the question
    speak(currentQuestion);
}

// ---------------- RECORD AUDIO ----------------
async function startListening() {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Initialize audio context and analyser for silence detection
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);
        analyser.fftSize = 256;
        
        // Initialize media recorder
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            processRecording();
        };
        
        // Start recording
        mediaRecorder.start();
        isRecording = true;
        recordingStartTime = Date.now();
        
        // Update UI
        document.getElementById('recordBtn').classList.add('hidden');
        document.getElementById('stopBtn').classList.remove('hidden');
        document.getElementById('recordingTimer').classList.remove('hidden');
        
        // Start timers and detection
        startTimer();
        startSilenceDetection();
        
        // Create or update recording GIF overlay
        let recordingOverlay = document.getElementById('recordingOverlay');
        
        if (!recordingOverlay) {
            recordingOverlay = document.createElement('div');
            recordingOverlay.id = 'recordingOverlay';
            recordingOverlay.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                background: rgba(0, 0, 0, 0.8);
                border-radius: 15px;
                padding: 15px;
                text-align: center;
                color: white;
                font-weight: bold;
                font-size: 14px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease-in;
                min-width: 150px;
            `;
            
            // Add recording GIF (using your specific GIF)
            const recordingGif = document.createElement('img');
            recordingGif.src = '/static/images/42787621ed6d40f0c30f0ae423fc572c.gif';
            recordingGif.alt = 'Recording...';
            recordingGif.style.cssText = `
                width: 50px;
                height: 50px;
                margin-bottom: 8px;
                border-radius: 50%;
                object-fit: cover;
                border: 2px solid #ff0000;
                box-shadow: 0 0 15px rgba(255, 0, 0, 0.5);
            `;
            
            // Add recording text
            const recordingText = document.createElement('div');
            recordingText.textContent = 'Recording...';
            recordingText.style.cssText = `
                font-size: 12px;
                margin-top: 5px;
                animation: pulse 1.5s infinite;
            `;
            
            recordingOverlay.appendChild(recordingGif);
            recordingOverlay.appendChild(recordingText);
            
            document.body.appendChild(recordingOverlay);
        }
        
        console.log("Recording started successfully");
        
    } catch (error) {
        console.error("Error accessing microphone:", error);
        alert("Unable to access microphone. Please check your browser permissions and try again.");
    }
}

function showRecordingGif() {
    // Create or update recording GIF overlay
    let recordingOverlay = document.getElementById('recordingOverlay');
    
    if (!recordingOverlay) {
        recordingOverlay = document.createElement('div');
        recordingOverlay.id = 'recordingOverlay';
        recordingOverlay.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            background: rgba(0, 0, 0, 0.8);
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease-in;
            min-width: 150px;
        `;
        
        // Add recording GIF (using your specific GIF)
        const recordingGif = document.createElement('img');
        recordingGif.src = '/static/images/42787621ed6d40f0c30f0ae423fc572c.gif';
        recordingGif.alt = 'Recording...';
        recordingGif.style.cssText = `
            width: 50px;
            height: 50px;
            margin-bottom: 8px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #ff0000;
            box-shadow: 0 0 15px rgba(255, 0, 0, 0.5);
        `;
        
        // Add recording text
        const recordingText = document.createElement('div');
        recordingText.textContent = 'Recording...';
        recordingText.style.cssText = `
            font-size: 12px;
            margin-top: 5px;
            animation: pulse 1.5s infinite;
        `;
        
        recordingOverlay.appendChild(recordingGif);
        recordingOverlay.appendChild(recordingText);
        
        document.body.appendChild(recordingOverlay);
    }
}

function hideRecordingGif() {
    const recordingOverlay = document.getElementById('recordingOverlay');
    if (recordingOverlay) {
        recordingOverlay.style.display = 'none';
        setTimeout(() => {
            recordingOverlay.remove();
        }, 300);
    }
}

function stopRecording() {
    if (!isRecording) return;
    
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }
    cleanupRecording();
}

function cleanupRecording() {
    isRecording = false;
    
    // Clear timers
    if (timerInterval) clearInterval(timerInterval);
    if (silenceTimer) clearTimeout(silenceTimer);
    
    // Stop audio tracks
    if (mediaRecorder && mediaRecorder.stream) {
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    
    // Close audio context
    if (audioContext) {
        audioContext.close();
    }
    
    // Reset UI - use correct element IDs and classes
    document.getElementById('recordBtn').classList.remove('hidden');
    document.getElementById('stopBtn').classList.add('hidden');
    document.getElementById('recordingTimer').classList.add('hidden');
    
    // Reset recording timer display
    const recordingTimerElement = document.getElementById("recordingTimer");
    if (recordingTimerElement) {
        recordingTimerElement.innerHTML = '<i class="fas fa-circle animate-pulse mr-2"></i>Recording: <span id="recordingTime">0</span>s';
    }
    
    // Hide recording overlay
    hideRecordingGif();
    
    // Reset variables for next recording
    mediaRecorder = null;
    audioChunks = [];
    audioContext = null;
    analyser = null;
    microphone = null;
}

function startTimer() {
    let seconds = 0;
    timerInterval = setInterval(() => {
        seconds++;
        const recordingTimerElement = document.getElementById("recordingTimer");
        if (recordingTimerElement) {
            recordingTimerElement.textContent = `Recording: ${seconds}s`;
        }
    }, 1000);
}

function startSilenceDetection() {
    let silenceCount = 0;
    const silenceThreshold = 0.01; // Adjust based on testing
    const checkInterval = 100; // Check every 100ms
    const maxSilenceTime = 5000; // 5 seconds of silence
    
    const checkSilence = () => {
        if (!isRecording) return;
        
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(dataArray);
        
        // Calculate average volume
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        const normalized = average / 255;
        
        if (normalized < silenceThreshold) {
            silenceCount += checkInterval;
            if (silenceCount >= maxSilenceTime) {
                console.log("Silence detected, stopping recording");
                stopRecording();
                return;
            }
        } else {
            silenceCount = 0; // Reset silence counter when speech is detected
        }
        
        if (isRecording) {
            silenceTimer = setTimeout(checkSilence, checkInterval);
        }
    };
    
    silenceTimer = setTimeout(checkSilence, checkInterval);
}

async function processRecording() {
    const blob = new Blob(audioChunks, { type: "audio/wav" });

    const formData = new FormData();
    formData.append("audio", blob, "audio.wav");

    // Show processing indicator and answer section
    document.getElementById("answerSection").classList.remove("hidden");
    document.getElementById("userAnswer").innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <div class="loading-spinner" style="font-size: 24px;">🔄</div>
            <p style="margin-top: 15px; color: #8b5cf6; font-weight: 600;">Processing your answer...</p>
            <p style="margin-top: 5px; color: #6b7280; font-size: 14px;">Converting speech to text and analyzing with AI</p>
        </div>
    `;

    try {
        const res = await fetch("/next", {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        console.log("NEXT RESPONSE:", data);

        if (data.error) {
            document.getElementById("userAnswer").innerHTML = "<b>You:</b> " + data.error;
            // Show next button even on error so user can try again
            document.getElementById('nextBtn').classList.remove('hidden');
            return;
        }

        // Display the transcribed answer
        currentAnswer = data.transcript;
        document.getElementById("userAnswer").innerHTML = "<b>You:</b> " + currentAnswer;

        if (data.score) {
            scores.push(data.score.total_score);
            localStorage.setItem("scores", JSON.stringify(scores));
        }

        if (data.end) {
            localStorage.setItem("final_percentage", data.percentage);
            window.location.href = "/result";
            return;
        }

        // Update to next question
        currentQuestion = data.next_question;
        document.getElementById("question").innerHTML = "<b>AI:</b> " + currentQuestion;
        
        speak(currentQuestion);
        
        // Show next button for user to continue
        document.getElementById('nextBtn').classList.remove('hidden');
        
    } catch (error) {
        console.error("Error processing recording:", error);
        document.getElementById("userAnswer").innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 24px;">❌</div>
                <p style="margin-top: 15px; color: #dc2626; font-weight: 600;">Processing Failed</p>
                <p style="margin-top: 5px; color: #6b7280; font-size: 14px;">Failed to process audio. Please try again.</p>
            </div>
        `;
        // Show next button even on error so user can try again
        document.getElementById('nextBtn').classList.remove('hidden');
    }
}

// ---------------- NEXT QUESTION ----------------
async function nextQuestion() {
    if (!interviewActive) return;
    
    // Hide next button and answer section
    document.getElementById('nextBtn').classList.add('hidden');
    document.getElementById('answerSection').classList.add('hidden');
    
    // Show recording controls for the next question
    document.getElementById('recordBtn').style.display = 'inline-block';
    document.getElementById('stopBtn').style.display = 'none';
    
    // The next question should already be displayed from transcribeAudio
    // This function only handles UI state changes
}

// ---------------- TRANSCRIBE AUDIO ----------------
async function transcribeAudio(audioUrl) {
    try {
        // Show processing indicator
        document.getElementById("userAnswer").innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <div class="loading-spinner" style="font-size: 24px;">🔄</div>
                <p style="margin-top: 15px; color: #8b5cf6; font-weight: 600;">Processing your answer...</p>
                <p style="margin-top: 5px; color: #6b7280; font-size: 14px;">Converting speech to text and analyzing with AI</p>
            </div>
        `;
        document.getElementById("answerSection").classList.remove("hidden");
        
        // Convert audio URL to blob
        const response = await fetch(audioUrl);
        const audioBlob = await response.blob();
        
        // Create FormData to send audio
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        
        const res = await fetch('/next', {
            method: 'POST',
            body: formData
        });
        
        const data = await res.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // File upload handler
        document.getElementById('resumeFile').addEventListener('change', function(e) {
            if (this.files.length > 0) {
                const file = this.files[0];
                const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
                const fileNameDisplay = document.getElementById('fileNameDisplay');
                
                if (file.size > 5 * 1024 * 1024) {
                    // File is over 5MB - show in RED
                    fileNameDisplay.className = 'mt-2 text-sm text-red-600 font-500';
                    fileNameDisplay.textContent = '✗ ' + file.name + ' (' + fileSizeMB + 'MB) - File size exceeds 5MB limit';
                } else {
                    // File is within 5MB limit - show in GREEN
                    fileNameDisplay.className = 'mt-2 text-sm text-green-600 font-500';
                    fileNameDisplay.textContent = '✓ ' + file.name + ' (' + fileSizeMB + 'MB) uploaded';
                }
            }
        });

        // Display user answer
        document.getElementById("userAnswer").innerHTML = "<b>You:</b> " + data.transcript;
        document.getElementById("answerSection").classList.remove("hidden");
        
        if (data.end) {
            // Interview ended, redirect to results
            setTimeout(() => {
                window.location.href = '/result';
            }, 2000);
        } else {
            // Update question with next question from LLM analysis
            if (data.next_question) {
                currentQuestion = data.next_question;
                document.getElementById("question").innerHTML = "<b>AI:</b> " + currentQuestion;
                speak(currentQuestion);
            }
            // Show next button
            document.getElementById('nextBtn').classList.remove('hidden');
        }
        
    } catch (error) {
        console.error("Error transcribing audio:", error);
        document.getElementById("userAnswer").innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 24px;">❌</div>
                <p style="margin-top: 15px; color: #dc2626; font-weight: 600;">Processing Failed</p>
                <p style="margin-top: 5px; color: #6b7280; font-size: 14px;">Failed to process audio. Please try again.</p>
            </div>
        `;
        alert("Error processing audio. Please try again.");
    }
}

// ---------------- TEXT TO SPEECH ----------------
function speak(text) {
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    // Create speech utterance
    const speech = new SpeechSynthesisUtterance(text);
    speech.rate = 0.95;
    
    // Try to speak, handling potential browser restrictions
    try {
        window.speechSynthesis.speak(speech);
    } catch (error) {
        console.log("Speech synthesis error:", error);
        // Fallback: just display the question without audio
    }
}

// ---------------- END INTERVIEW ----------------
async function endInterview() {
    try {
        console.log("DEBUG: Ending interview...");
        // Stop camera monitoring
        if (typeof stopCameraMonitoring === 'function') {
            stopCameraMonitoring();
        }
        
        const res = await fetch("/end", { method: "POST" });
        const data = await res.json();
        
        console.log("DEBUG: End interview response:", data);

        const percentage = ((data.average_score / 5) * 100).toFixed(2);

        localStorage.setItem("final_percentage", percentage);
        localStorage.setItem("scores", JSON.stringify(scores));

        window.location.href = "/result";
    } catch (error) {
        console.error("DEBUG: Error ending interview:", error);
        // Even if there's an error, try to navigate to result page
        window.location.href = "/result";
    }
} 