import re
import os

editor_path = r'D:\learn\job\automation_to_existing_video_editor\templates\editor.html'
adv_path = r'D:\learn\job\automation_to_existing_video_editor\templates\advanced_features.html'
app_path = r'D:\learn\job\automation_to_existing_video_editor\app.py'

with open(editor_path, 'r', encoding='utf-8') as f:
    editor_html = f.read()

with open(adv_path, 'r', encoding='utf-8') as f:
    adv_html = f.read()

# -----------------
# 1. Extract CSS
# -----------------
css_match = re.search(r'<style>(.*?)</style>', adv_html, re.DOTALL)
if css_match:
    adv_css = css_match.group(1)
    
    # Strip some common tags from adv_css that we don't want overwriting editor.html roots
    adv_css = re.sub(r':root\s*\{.*?\}', '', adv_css, flags=re.DOTALL)
    adv_css = re.sub(r'body\s*\{.*?\}', '', adv_css, flags=re.DOTALL)
    adv_css = re.sub(r'\*\s*\{.*?\}', '', adv_css, flags=re.DOTALL)
    adv_css = re.sub(r'\.navbar(?:-brand|).+?\{.*?\}', '', adv_css, flags=re.DOTALL)
    adv_css = re.sub(r'\.tab-bar.+?\{.*?\}', '', adv_css, flags=re.DOTALL)
    adv_css = re.sub(r'\.tab-btn.+?\{.*?\}', '', adv_css, flags=re.DOTALL)
    adv_css = re.sub(r'\.tab-panel.+?\{.*?\}', '', adv_css, flags=re.DOTALL)
    adv_css = re.sub(r'\.btn\s*\{.*?\}', '', adv_css, flags=re.DOTALL)
    adv_css = re.sub(r'\.btn-primary.+?\{.*?\}', '', adv_css, flags=re.DOTALL)
    adv_css = re.sub(r'\.btn-success.+?\{.*?\}', '', adv_css, flags=re.DOTALL)
    adv_css = re.sub(r'\.btn-danger.+?\{.*?\}', '', adv_css, flags=re.DOTALL)
    
    # Insert new css
    if '</style>' in editor_html:
        editor_html = editor_html.replace('</style>', adv_css + '\n    </style>')

# -----------------
# 2. Extract JS
# -----------------
js_match = re.search(r'<script>(.*?)</script>', adv_html, re.DOTALL)
if js_match:
    adv_js = js_match.group(1)
    # Remove tab switching logic
    adv_js = re.sub(r'function switchTab\(.*?\}', '', adv_js, flags=re.DOTALL)
    
    if '</script>\n</body>' in editor_html:
        editor_html = editor_html.replace('</script>\n</body>', adv_js + '\n    </script>\n</body>')
    elif '</script>\n</html>' in editor_html:
        editor_html = editor_html.replace('</script>\n</html>', adv_js + '\n    </script>\n</html>')
    else:
        # Fallback
        editor_html = editor_html.replace('</body>', '<script>\n' + adv_js + '\n</script>\n</body>')

# -----------------
# 3. HTML Content
# -----------------
def get_between(text, start, end):
    try:
        return text.split(start)[1].split(end)[0].strip()
    except IndexError:
        return ""

tabs = [
    ('masking', '<i class="fas fa-mask me-2"></i>Masking', get_between(adv_html, '<!-- ===================== FEATURE 1: MASKING ===================== -->', '<!-- END MASKING -->')),
    ('autocut', '<i class="fas fa-scissors me-2"></i>Bulk Mark & Auto-Cut', get_between(adv_html, '<!-- ===================== FEATURE 2: BULK MARK & AUTO-CUT ===================== -->', '<!-- END AUTO-CUT -->')),
    ('audio', '<i class="fas fa-sliders-h me-2"></i>Audio Effects', get_between(adv_html, '<!-- ===================== FEATURE 3: AUDIO EFFECTS ===================== -->', '<!-- END AUDIO EFFECTS -->')),
    ('keyframes', '<i class="fas fa-bezier-curve me-2"></i>Keyframes', get_between(adv_html, '<!-- FEATURE 4: KEYFRAMES -->', '<!-- FEATURE 5: MOTION BLUR -->')),
    ('motionblur', '<i class="fas fa-wind me-2"></i>Motion Blur', get_between(adv_html, '<!-- FEATURE 5: MOTION BLUR -->', '<!-- FEATURE 6: STYLE ANALYSIS -->')),
    ('styleanalysis', '<i class="fas fa-chart-line me-2"></i>Style Analysis', get_between(adv_html, '<!-- FEATURE 6: STYLE ANALYSIS -->', '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3'))
]

# Build Buttons
new_buttons = ""
for tab_id, icon_label, html in tabs:
    new_buttons += f'\n                    <button class="feature-btn" onclick="showFeature(\'{tab_id}\')">\n                        {icon_label}\n                    </button>'

# Build Content divs
new_content_divs = ""
for tab_id, icon_label, html in tabs:
    # change `<div id="tab-..." class="tab-panel active">` to `<div class="feature-content" id="...Content">`
    html = re.sub(r'<div id="tab-[a-zA-Z0-9_-]+" class="tab-panel(\s*active)?">', f'<div class="feature-content" id="{tab_id}Content">\n                    <h3>{icon_label}</h3>', html)
    new_content_divs += "\n\n                <!-- " + tab_id.upper() + " Content -->\n                " + html

# Insert Buttons
btn_insertion_marker = "<!-- New Feature Buttons -->"
if btn_insertion_marker in editor_html:
    editor_html = editor_html.replace(btn_insertion_marker, btn_insertion_marker + new_buttons)
else:
    # Fallback search for Dailymotion button end
    editor_html = editor_html.replace('</button>\n                </div>\n\n                <!-- Feature Contents -->', new_buttons + '\n                </div>\n\n                <!-- Feature Contents -->')

# Insert Feature Content Divs
content_insertion_marker = '<!-- Add Merge Videos Content -->'
if content_insertion_marker in editor_html:
    editor_html = editor_html.replace(content_insertion_marker, new_content_divs + '\n\n                ' + content_insertion_marker)

# -----------------
# 4. Remove Navbar Link
# -----------------
import re
editor_html = re.sub(r'<li class="nav-item">\s*<a class="nav-link" href="\{\{ url_for\(\'advanced_features\'\) \}\}">.*?advanced features.*?</a>\s*</li>', '', editor_html, flags=re.IGNORECASE|re.DOTALL)

# Write modified editor_html
with open(editor_path, 'w', encoding='utf-8') as f:
    f.write(editor_html)

# -----------------
# 5. Modify app.py
# -----------------
with open(app_path, 'r', encoding='utf-8') as f:
    app_py = f.read()

# remove advanced_features route entirely
app_py = re.sub(r'@app\.route\(\'/advanced-features\'\).*?def advanced_features\(\):.*?return render_template\(\'advanced_features\.html\'\)', '', app_py, flags=re.DOTALL)

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Merge completed successfully.")
