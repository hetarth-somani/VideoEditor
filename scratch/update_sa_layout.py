import re

with open('templates/editor.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Pattern for styleanalysisContent
sa_pattern = re.compile(r'<!-- STYLEANALYSIS Content -->\s*<div class="feature-content" id="styleanalysisContent">.*?</div>\s*<!-- Add Merge Videos Content -->', re.DOTALL)

new_sa = """<!-- STYLEANALYSIS Content -->
                <div class="feature-content" id="styleanalysisContent">
                    <div class="d-flex align-items-center justify-content-between mb-4 pb-2 border-bottom flex-wrap gap-2">
                        <div>
                            <h4 class="mb-1 fw-bold text-dark"><i class="fas fa-chart-line me-2 text-primary"></i>Style Analyzer & Replication Guide</h4>
                            <p class="text-muted mb-0 small">Automated analysis of video pacing, color palette, brightness, audio loudness, and step-by-step editing blueprint.</p>
                        </div>
                        <span class="badge bg-primary text-white px-3 py-2" style="font-size:0.75rem;"><i class="fas fa-check-circle me-1"></i>Deterministic Engine v2</span>
                    </div>

                    <div class="row g-4">
                        <!-- Sidebar: Controls -->
                        <div class="col-lg-3 col-md-4">
                            <div class="card p-3 mb-3" style="display:none;" id="sa-video-container">
                                <label class="form-label mb-1">Analyzing Clip:</label>
                                <video id="sa-video" controls style="width:100%; border-radius:6px; background:#0f172a; max-height:180px;"></video>
                            </div>
                            <div class="card p-3">
                                <h6 class="fw-semibold text-secondary mb-3"><i class="fas fa-sliders-h me-1 text-primary"></i> Analysis Controls</h6>
                                <div class="mb-3">
                                    <label class="form-label">Editor Skill Level</label>
                                    <select id="sa-skill-level" class="form-select form-select-sm">
                                        <option value="beginner">Beginner</option>
                                        <option value="intermediate" selected>Intermediate</option>
                                        <option value="advanced">Advanced</option>
                                    </select>
                                </div>
                                <button class="btn btn-primary w-100" id="sa-analyze-btn" onclick="saAnalyze()">
                                    <i class="fas fa-wand-magic-sparkles me-1"></i> Analyze Video Style
                                </button>
                                <div id="sa-progress-wrap" style="display:none; margin-top:0.75rem;">
                                    <div class="small text-muted mb-1" id="sa-progress-label">Analyzing...</div>
                                    <div class="progress" style="height:6px;">
                                        <div class="progress-bar progress-bar-striped progress-bar-animated" id="sa-progress-fill" style="width:0%"></div>
                                    </div>
                                </div>
                                <div class="d-flex flex-column gap-2 mt-3" id="sa-export-btns" style="display:none!important">
                                    <button class="btn btn-sm btn-outline-secondary text-start" onclick="saExportJSON()"><i class="fas fa-download me-2 text-primary"></i>Export JSON Report</button>
                                    <button class="btn btn-sm btn-outline-secondary text-start" onclick="saExportMarkdown()"><i class="fas fa-file-alt me-2 text-primary"></i>Export Markdown (.md)</button>
                                    <button class="btn btn-sm btn-outline-secondary text-start" onclick="saCopyGuide()"><i class="fas fa-copy me-2 text-primary"></i>Copy Replication Guide</button>
                                </div>
                            </div>
                        </div>

                        <!-- Main Analysis Results Dashboard (Full-width grid) -->
                        <div class="col-lg-9 col-md-8">
                            <div id="sa-empty" class="text-center text-muted p-5 card">
                                <i class="fas fa-chart-pie fa-3x mb-3 opacity-50"></i>
                                <h6 class="fw-semibold text-dark mb-1">No Style Report Generated Yet</h6>
                                <p class="small text-muted mb-0">Upload a video in the Original Video card above and click "Analyze Video Style".</p>
                            </div>

                            <div id="sa-results" style="display:none">
                                <!-- Top Row: 4 Metric Cards -->
                                <div class="row g-3 mb-3">
                                    <div class="col-xl-3 col-sm-6">
                                        <div class="card p-3 text-center h-100">
                                            <span class="small text-muted fw-medium d-block mb-1">Overall Style Score</span>
                                            <div style="position:relative; width:100px; height:100px; margin:0 auto;">
                                                <canvas id="sa-score-canvas" width="100" height="100" style="display:block;"></canvas>
                                                <div id="sa-score-label" style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-size:1.25rem; font-weight:700; color:var(--primary-color);">—</div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-xl-3 col-sm-6">
                                        <div class="card p-3 h-100">
                                            <span class="small text-muted fw-medium d-block mb-1"><i class="fas fa-tachometer-alt me-1 text-primary"></i> Pacing & Rhythm</span>
                                            <div id="sa-pacing-info" class="mt-2" style="font-size:0.85rem;"></div>
                                        </div>
                                    </div>
                                    <div class="col-xl-3 col-sm-6">
                                        <div class="card p-3 h-100">
                                            <span class="small text-muted fw-medium d-block mb-1"><i class="fas fa-eye me-1 text-primary"></i> Visual Profile</span>
                                            <div id="sa-visual-metrics" class="mt-2" style="font-size:0.825rem;"></div>
                                        </div>
                                    </div>
                                    <div class="col-xl-3 col-sm-6">
                                        <div class="card p-3 h-100">
                                            <span class="small text-muted fw-medium d-block mb-1"><i class="fas fa-volume-up me-1 text-primary"></i> Audio Profile</span>
                                            <div id="sa-audio-info" class="mt-2" style="font-size:0.825rem;"></div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Middle Row: Pacing Timeline Chart & Color Palette -->
                                <div class="row g-3 mb-3">
                                    <div class="col-md-7">
                                        <div class="card p-3 h-100">
                                            <div class="d-flex justify-content-between align-items-center mb-2">
                                                <span class="fw-semibold text-secondary small"><i class="fas fa-chart-bar me-1 text-primary"></i> Shot Length & Cuts Timeline</span>
                                                <span id="sa-pacing-note" class="small text-muted"></span>
                                            </div>
                                            <canvas id="sa-pacing-canvas" height="90" style="width:100%; background:#0f172a; border-radius:6px;"></canvas>
                                        </div>
                                    </div>
                                    <div class="col-md-5">
                                        <div class="card p-3 h-100">
                                            <span class="fw-semibold text-secondary small mb-2 d-block"><i class="fas fa-palette me-1 text-primary"></i> Dominant Color Palette</span>
                                            <div id="sa-palette" class="d-flex gap-2 flex-wrap mt-2"></div>
                                            <span class="small text-muted mt-2 d-block" style="font-size:0.75rem;">Click any color swatch to copy hex value</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- Recommendations Card -->
                                <div class="card p-3 mb-3">
                                    <h6 class="fw-semibold text-secondary mb-2"><i class="fas fa-lightbulb me-1 text-warning"></i> Editing Recommendations</h6>
                                    <ul id="sa-recommendations" class="mb-0 ps-3" style="font-size:0.85rem;"></ul>
                                </div>

                                <!-- Replication Guide Card -->
                                <div id="sa-guide-wrap" class="card p-3 mb-3" style="display:none">
                                    <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
                                        <h6 class="fw-semibold text-dark mb-0"><i class="fas fa-book me-2 text-primary"></i>Step-by-Step Replication Guide</h6>
                                        <span class="badge bg-light text-muted border">Evidence-Based</span>
                                    </div>
                                    <div class="row g-3">
                                        <div class="col-md-6"><div id="sa-guide-project-setup" class="sa-guide-section"></div></div>
                                        <div class="col-md-6"><div id="sa-guide-shot-recipe" class="sa-guide-section"></div></div>
                                        <div class="col-md-6"><div id="sa-guide-edit-blueprint" class="sa-guide-section"></div></div>
                                        <div class="col-md-6"><div id="sa-guide-color-recipe" class="sa-guide-section"></div></div>
                                        <div class="col-md-6"><div id="sa-guide-audio-recipe" class="sa-guide-section"></div></div>
                                        <div class="col-md-6"><div id="sa-guide-export-settings" class="sa-guide-section"></div></div>
                                        <div class="col-12"><div id="sa-guide-editor-steps" class="sa-guide-section"></div></div>
                                    </div>
                                </div>

                                <!-- Full Analysis Data Table -->
                                <div class="card p-3">
                                    <h6 class="fw-semibold text-secondary mb-2"><i class="fas fa-table me-1 text-primary"></i> Full Video Metadata & Metrics</h6>
                                    <div id="sa-full-table" class="table-responsive"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Add Merge Videos Content -->"""

html = sa_pattern.sub(new_sa, html, count=1)
open('templates/editor.html', 'w', encoding='utf-8').write(html)
print('Style Analyzer layout updated successfully!')
