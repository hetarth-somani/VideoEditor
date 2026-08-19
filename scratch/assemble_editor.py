import re

with open('templates/editor.html', 'r', encoding='utf-8') as f:
    orig = f.read()

# Split before <div class="container">
container_idx = orig.find('<div class="container">')
head_nav = orig[:container_idx]

# Split scripts
script_idx = orig.find('<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js">')
middle_body = orig[container_idx:script_idx]
scripts = orig[script_idx:]

# Extract feature buttons
fb_match = re.search(r'<div class="feature-buttons">(.*?)</div>\s*<!-- Feature Contents -->', middle_body, re.DOTALL)
feature_buttons_html = fb_match.group(1).strip() if fb_match else ""

# Extract prompt section
prompt_match = re.search(r'<div class="prompt-section">(.*?)</div>\s*<!-- Add Pexels', middle_body, re.DOTALL)
if not prompt_match:
    prompt_match = re.search(r'<div class="prompt-section">(.*?)</div>\s*<!--', middle_body, re.DOTALL)

prompt_section_inner = prompt_match.group(1).strip() if prompt_match else ""

# Remove prompt section from feature contents
body_without_prompt = middle_body.replace(f'<div class="prompt-section">{prompt_section_inner}</div>', '')

# Extract all feature content blocks: from <!-- Feature Contents --> to the end of col-lg-8
fc_start = body_without_prompt.find('<!-- Feature Contents -->')
fc_end = body_without_prompt.find('<div class="col-lg-4">')
if fc_end == -1:
    fc_end = body_without_prompt.find('<!-- Output Section -->')

feature_contents_all = body_without_prompt[fc_start:fc_end].strip()
# Clean any trailing </div> from col-lg-8
feature_contents_all = re.sub(r'\s*</div>\s*$', '', feature_contents_all)

new_layout = f"""    <div class="editor-container">
        <!-- Top Row: Balanced Equal-Sized Video Previews (50% / 50%) -->
        <div class="row g-4 mb-4">
            <!-- Left Column: Input Video (50%) -->
            <div class="col-lg-6">
                <div class="card h-100 p-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div class="card-header-title">
                            <i class="fas fa-file-video text-primary"></i> Original Video
                        </div>
                        <span id="inputVideoBadge" class="badge bg-light text-muted border" style="font-size:0.75rem;">No video uploaded</span>
                    </div>
                    <div class="upload-area" id="uploadArea">
                        <i class="fas fa-cloud-upload-alt fa-3x mb-2 text-muted"></i>
                        <p class="mb-1 fw-semibold text-dark">Click to upload video or drag & drop</p>
                        <p class="small text-muted mb-0">Supports MP4, MOV, AVI, WebM</p>
                    </div>
                    <div class="video-container mt-2" id="inputVideoContainer" style="display: none;">
                        <video id="videoPreview" class="video-preview" controls></video>
                    </div>
                </div>
            </div>

            <!-- Right Column: Processed Output Preview (50%) -->
            <div class="col-lg-6">
                <div class="card h-100 p-3 output-section">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div class="card-header-title">
                            <i class="fas fa-play-circle text-primary"></i> Output Preview
                        </div>
                        <div class="d-flex gap-2">
                            <button id="undoBtn" class="btn btn-outline-secondary btn-sm" onclick="undoLastEffect()" disabled>
                                <i class="fas fa-undo me-1"></i> Undo
                            </button>
                        </div>
                    </div>
                    <div class="video-container" id="outputVideoContainer">
                        <video id="outputPreview" class="video-preview" controls style="display: none;">
                            Your browser does not support the video tag.
                        </video>
                        <div id="outputPlaceholder" class="text-center text-muted p-4">
                            <i class="fas fa-film fa-3x mb-2 opacity-50 text-muted"></i>
                            <p class="mb-1 fw-medium text-dark">Processed video preview will appear here</p>
                            <p class="small text-muted mb-0">Select an edit or effect from the tools below</p>
                        </div>
                    </div>
                    <div class="progress-container mt-3" style="display: none;">
                        <div class="progress" style="height: 6px;">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%"></div>
                        </div>
                        <div class="status-message text-center mt-2 small text-muted"></div>
                    </div>
                    <a id="downloadBtn" class="btn btn-primary w-100 mt-3" style="display: none;">
                        <i class="fas fa-download me-2"></i>Download Processed Video
                    </a>
                </div>
            </div>
        </div>

        <!-- Main Tools & Features Container (Full Width) -->
        <div class="row">
            <div class="col-12">
                <div class="card p-3 mb-4">
                    <!-- Feature Buttons Toolbar -->
                    <div class="feature-buttons mb-3 pb-3 border-bottom">
                        {feature_buttons_html}
                    </div>

                    <!-- Active Feature Contents (Placed at the TOP of the tools card!) -->
                    <div class="feature-contents-wrapper">
                        {feature_contents_all}
                    </div>

                    <!-- Text Commands (Pushed to the very BOTTOM of tools card!) -->
                    <div class="prompt-section mt-4 pt-3 border-top">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="card-header-title">
                                <i class="fas fa-terminal text-primary"></i> Text Commands
                            </div>
                            <button class="btn btn-sm btn-outline-secondary" type="button" onclick="showPromptHelp()">
                                <i class="fas fa-question-circle me-1"></i> Toggle All Commands
                            </button>
                        </div>
                        <div class="prompt-input mb-2">
                            <input type="text" id="promptInput" placeholder="Enter your command (e.g. 'trim start=10 end=30', 'speed factor=1.5', 'color_grade preset=cinematic')" class="form-control">
                            <button onclick="processPrompt()" class="btn btn-primary px-4">
                                <i class="fas fa-paper-plane me-1"></i> Process
                            </button>
                        </div>
                        <div class="prompt-help mt-3">
                            <div id="basicCommands">
                                <strong>Basic Operations:</strong>
                                <ul class="mb-2">
                                    <li><code>trim start=10 end=30</code> - Trim video from 10s to 30s</li>
                                    <li><code>resize width=1920 height=1080</code> - Resize to 1920x1080</li>
                                    <li><code>speed factor=2.0</code> - Change speed (2x faster)</li>
                                    <li><code>extract_audio format=mp3</code> - Extract audio as MP3</li>
                                </ul>
                                <strong>Effects & Color:</strong>
                                <ul>
                                    <li><code>color_grade preset=cinematic</code> - Apply color preset</li>
                                    <li><code>effect type=blur strength=2</code> - Apply blur effect</li>
                                    <li><code>overlay type=text content="Hello" position=center</code> - Add text</li>
                                </ul>
                            </div>
                            <div id="allCommands" style="display: none;">
                                <div class="row">
                                    <div class="col-md-6">
                                        <strong>Basic Operations:</strong>
                                        <ul style="font-size: 0.85em;">
                                            <li><code>trim start=X end=Y</code></li>
                                            <li><code>resize width=X height=Y</code></li>
                                            <li><code>speed factor=X</code></li>
                                            <li><code>extract_audio format=mp3|wav</code></li>
                                        </ul>
                                        <strong>Color & Effects:</strong>
                                        <ul style="font-size: 0.85em;">
                                            <li><code>color_grade preset=cinematic|vintage|warm|cool|noir|vibrant</code></li>
                                            <li><code>color_grade brightness=X contrast=Y saturation=Z</code></li>
                                            <li><code>effect type=blur|sepia|negative|mirror|pixelate|edge_detection strength=X</code></li>
                                            <li><code>speed_ramp start=X end=Y factor=Z</code></li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <strong>Animation & Text:</strong>
                                        <ul style="font-size: 0.85em;">
                                            <li><code>animation type=zoom|pan|fade|rotate start=X end=Y scale=Z</code></li>
                                            <li><code>animation type=pan direction=left|right|up|down</code></li>
                                            <li><code>overlay type=text content="Text" position=center|top|bottom</code></li>
                                            <li><code>overlay type=text content="Text" x=X y=Y duration=W</code></li>
                                        </ul>
                                        <strong>Multi-Video Commands:</strong>
                                        <ul style="font-size: 0.85em;">
                                            <li><code>merge_videos transition=fade duration=2</code> (requires multiple files)</li>
                                            <li><code>transition type=dissolve duration=1.5</code> (requires multiple files)</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
"""

# Now update scripts to handle Undo stack and clean preview
updated_scripts = scripts

# Replace the initial variable declarations
var_decl_pattern = r'let currentVideo = null;\s*let processedVideo = null;.*?\n'
new_var_decl = """let originalVideo = null;
        let currentVideo = null;
        let processedVideo = null;
        let videoHistory = []; // Stack of previous video states
        let mergeFilesList = [];

        function updateUndoButton() {
            const undoBtn = document.getElementById('undoBtn');
            if (!undoBtn) return;
            if (videoHistory.length > 0) {
                undoBtn.disabled = false;
                undoBtn.innerHTML = `<i class="fas fa-undo me-1"></i> Undo (${videoHistory.length})`;
                undoBtn.title = `Undo last effect (revert to previous video)`;
            } else {
                undoBtn.disabled = true;
                undoBtn.innerHTML = `<i class="fas fa-undo me-1"></i> Undo`;
                undoBtn.title = "No previous video state to undo";
            }
        }

        function undoLastEffect() {
            if (videoHistory.length === 0) return;

            const prevState = videoHistory.pop();
            currentVideo = prevState.file || originalVideo;
            processedVideo = (videoHistory.length > 0) ? currentVideo : null;

            const outputPreview = document.getElementById('outputPreview');
            const outputPlaceholder = document.getElementById('outputPlaceholder');
            const downloadBtn = document.getElementById('downloadBtn');

            if (prevState.url && prevState.url !== 'original') {
                if (outputPreview) {
                    outputPreview.src = prevState.url + (prevState.url.includes('?') ? '&' : '?') + 't=' + new Date().getTime();
                    outputPreview.style.display = 'block';
                    outputPreview.load();
                }
                if (outputPlaceholder) outputPlaceholder.style.display = 'none';
                if (downloadBtn) {
                    downloadBtn.href = prevState.url;
                    downloadBtn.style.display = 'block';
                    downloadBtn.download = prevState.name || 'reverted_video.mp4';
                }
            } else {
                // Reverted back to original state
                if (outputPreview) {
                    outputPreview.src = '';
                    outputPreview.style.display = 'none';
                }
                if (outputPlaceholder) outputPlaceholder.style.display = 'block';
                if (downloadBtn) downloadBtn.style.display = 'none';
            }

            syncFeatureVideos(currentVideo);
            updateUndoButton();
            updateProgress(100, `Reverted to previous state (${prevState.name || 'original'})`);
        }
"""

updated_scripts = re.sub(var_decl_pattern, new_var_decl, updated_scripts, count=1)

# Update getVideoToProcess
get_video_pattern = r'function getVideoToProcess\(\)\s*\{.*?return processedVideo \|\| currentVideo;\s*\}'
new_get_video = """function getVideoToProcess() {
            return currentVideo || originalVideo;
        }"""
updated_scripts = re.sub(get_video_pattern, new_get_video, updated_scripts, flags=re.DOTALL)

# Update showOutput to push to history stack and manage preview
show_output_pattern = r'function showOutput\(url\)\s*\{.*?updateProgress\(100, \'Processing completed successfully!\'\);\s*\}'
new_show_output = """function showOutput(url) {
            const outputPreview = document.getElementById('outputPreview');
            const outputPlaceholder = document.getElementById('outputPlaceholder');
            const downloadBtn = document.getElementById('downloadBtn');

            // Save previous active video to history stack
            if (currentVideo) {
                const prevUrl = (outputPreview && outputPreview.src && outputPreview.style.display !== 'none') 
                                ? outputPreview.src 
                                : (originalVideo ? URL.createObjectURL(originalVideo) : 'original');
                videoHistory.push({
                    file: currentVideo,
                    url: prevUrl,
                    name: currentVideo.name || 'previous_step.mp4'
                });
            }

            fetch(url)
                .then(response => response.blob())
                .then(blob => {
                    const outName = url.split('/').pop() || 'processed_video.mp4';
                    processedVideo = new File([blob], outName, { type: blob.type || 'video/mp4' });
                    currentVideo = processedVideo;
                    syncFeatureVideos(processedVideo);

                    if (outputPreview) {
                        outputPreview.src = url + '?t=' + new Date().getTime();
                        outputPreview.style.display = 'block';
                        outputPreview.load();
                    }
                    if (outputPlaceholder) {
                        outputPlaceholder.style.display = 'none';
                    }

                    if (downloadBtn) {
                        downloadBtn.href = url;
                        downloadBtn.style.display = 'block';
                        downloadBtn.download = outName;
                    }

                    updateUndoButton();
                })
                .catch(error => {
                    console.error('Error fetching processed video:', error);
                    updateProgress(0, 'Error loading video. Please try again.');
                });

            showProgress(false);
            updateProgress(100, 'Processing completed successfully!');
        }"""

updated_scripts = re.sub(show_output_pattern, new_show_output, updated_scripts, flags=re.DOTALL)

# Update uploadArea listener in script
upload_listener_pattern = r'uploadArea\.addEventListener\(\'click\', \(\) => \{.*?uploadArea\.addEventListener\(\'drop\', \(e\) => \{.*?\}\);'

new_upload_listener = """function handleFileSelection(file) {
            if (!file) return;
            originalVideo = file;
            currentVideo = file;
            processedVideo = null;
            videoHistory = [];
            updateUndoButton();

            const uploadArea = document.getElementById('uploadArea');
            const inputVideoContainer = document.getElementById('inputVideoContainer');
            const videoPreview = document.getElementById('videoPreview');
            const inputBadge = document.getElementById('inputVideoBadge');

            if (inputBadge) {
                inputBadge.textContent = file.name;
                inputBadge.className = 'badge bg-primary text-white';
            }

            if (uploadArea) {
                uploadArea.innerHTML = `
                    <div class="d-flex align-items-center justify-content-between">
                        <div class="text-start">
                            <span class="small text-muted d-block">Selected:</span>
                            <span class="fw-semibold text-dark">${file.name}</span>
                        </div>
                        <span class="btn btn-sm btn-outline-secondary"><i class="fas fa-exchange-alt me-1"></i>Change Video</span>
                    </div>
                `;
            }

            if (videoPreview) {
                videoPreview.src = URL.createObjectURL(file);
                videoPreview.style.display = 'block';
                videoPreview.load();
            }
            if (inputVideoContainer) {
                inputVideoContainer.style.display = 'block';
            }

            syncFeatureVideos(file);
        }

        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.addEventListener('click', () => {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'video/*,audio/*';
                input.onchange = (e) => handleFileSelection(e.target.files[0]);
                input.click();
            });

            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = 'var(--primary-color)';
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.style.borderColor = '#cbd5e1';
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = '#cbd5e1';
                handleFileSelection(e.dataTransfer.files[0]);
            });
        }"""

updated_scripts = re.sub(upload_listener_pattern, new_upload_listener, updated_scripts, flags=re.DOTALL)

# Combine everything
final_html = head_nav + new_layout + updated_scripts

open('templates/editor.html', 'w', encoding='utf-8').write(final_html)
print('templates/editor.html successfully updated!')
