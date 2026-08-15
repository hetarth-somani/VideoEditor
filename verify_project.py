import os
import time
import sys

try:
    from app import execute_trim_command, execute_speed_ramp_command, execute_effect_command, execute_animation_command
    
    # Check if test.mp4 exists
    test_video = 'test.mp4'
    if not os.path.exists(test_video):
        print("test.mp4 not found. Creating a dummy 1-second video for testing...")
        os.system("ffmpeg -f lavfi -i testsrc=duration=1:size=640x360:rate=30 -c:v libx264 -y test.mp4")
    
    print("Testing Trim Command...")
    ts = int(time.time())
    res = execute_trim_command('trim start=0 end=1', test_video, ts)
    print("Trim Result:", res)
    
    if res.get('success'):
        trimmed_video = os.path.join('output', res['output_file'])
        # If output folder is different, try to find it
        if not os.path.exists(trimmed_video):
            # check static/output or outputs
            if os.path.exists(os.path.join('outputs', res['output_file'])):
                trimmed_video = os.path.join('outputs', res['output_file'])
            elif os.path.exists(os.path.join('static', 'output', res['output_file'])):
                trimmed_video = os.path.join('static', 'output', res['output_file'])
                
        print(f"Using {trimmed_video} for further tests to save time.")
        
        print("\nTesting Speed Ramp Command...")
        res_speed = execute_speed_ramp_command('speed_ramp start=0 end=1 factor=2.0', trimmed_video, ts+1)
        print("Speed Ramp Result:", res_speed)
        
        print("\nTesting Effect Command...")
        res_effect = execute_effect_command('effect type=blur strength=2', trimmed_video, ts+2)
        print("Effect Result:", res_effect)
        
        print("\nTesting Animation Command...")
        res_anim = execute_animation_command('animation type=zoom_in', trimmed_video, ts+3)
        print("Animation Result:", res_anim)
        
        if res_speed.get('success') and res_effect.get('success') and res_anim.get('success'):
            print("\n✅ All automated video processing features are working fully!")
        else:
            print("\n❌ Some features failed.")
            sys.exit(1)
    else:
        print("\n❌ Trim failed, cannot proceed.")
        sys.exit(1)
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
