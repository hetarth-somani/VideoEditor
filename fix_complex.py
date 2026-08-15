import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# --- 1. Fix analyze_style JSON Response ---
new_analyze_style_json = """
        result_data = {
            'success': True,
            'score': score,
            'duration': duration,
            'resolution': resolution,
            'fps': fps,
            'has_audio': bool(a_stream),
            'color': {
                'palette': palette,
                'temperature': color_temp,
                'saturation': 1.0
            },
            'pacing': {
                'cuts_per_minute': cuts_per_minute,
                'total_cuts': total_cuts,
                'avg_clip_length': avg_clip_length,
                'label': pacing_label
            },
            'recommendations': recommendations
        }
        return jsonify(result_data)
"""
text = re.sub(r'result_data = \{\s*\'success\': True,\s*\'score\': score,\s*\'palette\': palette,\s*\'duration\': duration,\s*\'resolution\': resolution,\s*\'fps\': fps,\s*\'color_temperature\': color_temp,.*?return jsonify\(result_data\)', new_analyze_style_json.strip() + "\n", text, flags=re.DOTALL)

# --- 2. Fix apply_mask to generate Pillow masks ---
# Replace the entire vf_parts drawbox loop in apply_mask
mask_logic = """
    # Create mask using Python Pillow
    from PIL import Image, ImageDraw
    import cv2 

    # We will build a mask image in Python then alphamerge it in FFMPEG!
    # Because ffmpeg makes it incredibly complex to draw circles/polygons dynamically.
    
    # First query video resolution
    vid_info = get_video_info(input_path)
    streams = vid_info.get('streams', [])
    v_stream = next((s for s in streams if s['codec_type'] == 'video'), None)
    W = int(v_stream.get('width', 1920)) if v_stream else 1920
    H = int(v_stream.get('height', 1080)) if v_stream else 1080
    if W == 0 or H == 0:
        W, H = 1920, 1080

    mask_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(mask_img)

    for m in masks_list:
        color_hex = m.get('color', '#6c63ff').lstrip('#')
        opacity = float(m.get('opacity', 0.7))
        alpha = int(opacity * 255)
        # Handle rgba properly
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)

        mtype = m.get('type', 'rect')
        if mtype == 'rect':
            cx, cy = float(m.get('x',0)), float(m.get('y',0))
            cw, ch = float(m.get('w',0)), float(m.get('h',0))
            x1, y1 = (cx / 480.0) * W, (cy / 280.0) * H
            x2, y2 = ((cx+cw) / 480.0) * W, ((cy+ch) / 280.0) * H
            draw.rectangle([min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2)], fill=(r,g,b,alpha))

        elif mtype == 'circle':
            ccx, ccy = float(m.get('cx',0)), float(m.get('cy',0))
            rx, ry = float(m.get('rx',0)), float(m.get('ry',0))
            x1, y1 = ((ccx - rx) / 480.0) * W, ((ccy - ry) / 280.0) * H
            x2, y2 = ((ccx + rx) / 480.0) * W, ((ccy + ry) / 280.0) * H
            draw.ellipse([x1, y1, x2, y2], fill=(r,g,b,alpha))

        else:
            # Polygon / Freehand
            pts = m.get('pts', [])
            if pts:
                mapped_pts = [((p.get('x',0) / 480.0) * W, (p.get('y',0) / 280.0) * H) for p in pts]
                draw.polygon(mapped_pts, fill=(r,g,b,alpha))

    mask_path = os.path.join(app.config['UPLOAD_FOLDER'], f"mask_img_{timestamp}.png")
    mask_img.save(mask_path)

    cmd = [
        'ffmpeg', '-y', '-i', input_path, '-i', mask_path,
        '-filter_complex', '[0:v][1:v]overlay=0:0',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'copy', output_path
    ]
    success, msg = run_ffmpeg_command(cmd)
"""
text = re.sub(r'# Build FFmpeg drawbox/drawtext filter chain from mask list.*?cmd = \[\s*\'ffmpeg\', \'-y\', \'-i\', input_path,\s*\'-vf\', vf_filter,\s*\'-c:v\', \'libx264\', \'-preset\', \'fast\', \'-crf\', \'23\',\s*\'-c:a\', \'copy\', output_path\s*\]\s*success, msg = run_ffmpeg_command\(cmd\)', mask_logic.strip(), text, flags=re.DOTALL)


# --- 3. Fix apply_keyframes formulas ---
kf_logic = """
            # Advanced temporal formulas for animations across all keyframes using sendcmd or 't' evaluate!
            # The previous approach only grabbed first and last.
            # Using 't' variables to do linear interpolation over multiples:
            # We'll construct an IF chain in FFmpeg Math
            exprs = []
            for i in range(len(keyframes) - 1):
                k1 = keyframes[i]
                k2 = keyframes[i+1]
                t1 = float(k1.get('time', 0)) / 1000.0
                t2 = float(k2.get('time', 0)) / 1000.0
                v1 = float(k1.get('value', 0))
                v2 = float(k2.get('value', 0))
                if t2 > t1:
                    slope = (v2 - v1) / (t2 - t1)
                    eq = f"({v1}+({slope})*(t-{t1}))"
                    cond = f"between(t,{t1},{t2})"
                    exprs.append(f"if({cond},{eq},")
                    
            if exprs:
                # Cap the expression
                v_last = float(keyframes[-1].get('value', 0))
                t_last = float(keyframes[-1].get('time', 0)) / 1000.0
                full_expr = "".join(exprs) + f"if(gt(t,{t_last}),{v_last},{float(keyframes[0].get('value',0))})" + (")" * len(exprs))
            else:
                full_expr = str(float(keyframes[0].get('value', 0)))

            if prop == 'opacity':
                # Convert the expression into an alpha layer overlay format OR colorchannelmixer
                vf_filter = f"colorchannelmixer=aa='{full_expr}'"
            elif prop == 'scale':
                vf_filter = f"zoompan=z='{full_expr}':d=1:s=iw'x'ih"
            elif prop == 'blur':
                vf_filter = f"boxblur=luma_radius='{full_expr}':luma_power=1"
            elif prop == 'rotation':
                vf_filter = f"rotate=a='{full_expr}*PI/180'"
            else:
                vf_filter = "null"
        else:
            vf_filter = "null"

    cmd = [
"""
text = re.sub(r'if prop == \'opacity\':\s*# Implement opacity via fade effects.*else:\s*# Default: gentle zoom for any other property\s*vf_filter = "zoompan=z=\'min\(zoom\+0.0015,1.5\)\':d=125"\s*else:\s*# No valid keyframes: apply a gentle zoom-pan as demonstration\s*vf_filter = "zoompan=z=\'min\(zoom\+0.0015,1.5\)\':d=125"\s*cmd = \[', kf_logic.strip("\n"), text, flags=re.DOTALL)


with open('app.py', 'w', encoding='utf-8') as f: f.write(text)
