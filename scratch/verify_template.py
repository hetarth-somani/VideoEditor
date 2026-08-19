with open('templates/editor.html', 'r', encoding='utf-8') as f:
    editor_html = f.read()

checks = [
    ("Equal size video previews present (col-lg-6 for input & output)", 'col-lg-6' in editor_html and 'id="videoPreview"' in editor_html and 'id="outputPreview"' in editor_html),
    ("Undo button present in Output Preview header", 'id="undoBtn"' in editor_html and 'onclick="undoLastEffect()"' in editor_html),
    ("useProcessedVideo checkbox removed", 'id="useProcessedVideo"' not in editor_html),
    ("Style Analyzer spans full width dashboard", 'id="styleanalysisContent"' in editor_html and 'id="sa-results"' in editor_html),
    ("Text Commands section is at the bottom", editor_html.rfind('class="prompt-section') > editor_html.find('class="feature-contents-wrapper')),
    ("Undo JavaScript stack functions implemented", 'function updateUndoButton()' in editor_html and 'function undoLastEffect()' in editor_html),
    ("Clean, subtle CSS variables configured", '--background-color: #f8fafc;' in editor_html and '--primary-color: #2563eb;' in editor_html)
]

print("=== TEMPLATE VERIFICATION CHECKS ===")
all_pass = True
for name, passed in checks:
    status = "PASS" if passed else "FAIL"
    if not passed: all_pass = False
    print(f"[{status}] {name}")

print(f"\nOverall template status: {'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")
