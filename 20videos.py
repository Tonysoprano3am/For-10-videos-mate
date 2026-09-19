import td

# 1. CLEANUP ENGINE (Clears existing nodes to prevent overlapping)
root = op('/project1') if op('/project1') else op('/')
for child in root.children:
    child.destroy()

# =========================================================================
# 2. AUDIO CORE CHOPs (Isolates kicks and snares to generate 0/1 triggers)
# =========================================================================
audio_in = root.create(audiofileInCHOP, 'audio_source')
audio_in.par.file = "" # <-- Click this node in TouchDesigner to upload your audio track

# Kick Drum Track (Low Frequencies)
low_pass = root.create(audiofilterCHOP, 'kick_filter')
low_pass.connect(audio_in)
low_pass.par.filter = 'lowpass'
low_pass.par.cutoff = 150

kick_analyze = root.create(audioanalyzeCHOP, 'kick_analyze')
kick_analyze.connect(low_pass)
kick_analyze.par.function = 'rmspower'

kick_logic = root.create(logicCHOP, 'kick_trigger')
kick_logic.connect(kick_analyze)
kick_logic.par.convert = 'offon'
kick_logic.par.offonhigh = 0.15

# Snare Roll Track (High Frequencies)
high_pass = root.create(audiofilterCHOP, 'snare_filter')
high_pass.connect(audio_in)
high_pass.par.filter = 'highpass'
high_pass.par.cutoff = 2000

snare_analyze = root.create(audioanalyzeCHOP, 'snare_analyze')
snare_analyze.connect(high_pass)
snare_analyze.par.function = 'rmspower'

# =========================================================================
# 3. RANDOMIZATION ENGINE CHOPs (Ensures every glitch is unique)
# =========================================================================
beat_count = root.create(countCHOP, 'beat_counter')
beat_count.connect(kick_logic)

glitch_rand = root.create(randomCHOP, 'glitch_randomizer')
glitch_rand.connect(beat_count)

# =========================================================================
# 4. 10x VIDEO SOURCES & SELECTION ENGINE (Cycles clips 1-10 on kick drums)
# =========================================================================
video_switch = root.create(switchTOP, 'video_switcher')

# Automatically loops and builds 10 separate Movie File In nodes
NUM_VIDEOS = 10
for i in range(NUM_VIDEOS):
    vid_node = root.create(moviefileInTOP, f'video_source_{i+1}')
    vid_node.par.file = "" # <-- Open each node to upload your individual clips
    video_switch.connect(vid_node, i)

# Audio reaction: Kick drum math expression cycles through all 10 indices smoothly (0 to 9)
video_switch.par.index.expr = f"op('beat_counter')['count'] % {NUM_VIDEOS}" 

# =========================================================================
# 5. GLITCH ENGINE & STUTTER TOPs (Shatters video via snare rolls)
# =========================================================================
glitch_noise = root.create(noiseTOP, 'glitch_noise_pattern')
glitch_noise.par.resolutionw = 1920
glitch_noise.par.resolutionh = 1080
glitch_noise.par.monochrome = 0
# Audio reaction: Randomize the glitch texture grid shape dynamically on each beat
glitch_noise.par.seed.expr = "int(op('glitch_randomizer')['chan1'] * 1000)"
glitch_noise.par.period.expr = "0.05 + (op('snare_analyze')['chan1'] * 2)"

displace_glitch = root.create(displaceTOP, 'displacement_engine')
displace_glitch.connect(video_switch, 0)
displace_glitch.connect(glitch_noise, 1)
displace_glitch.par.displaceymode = 'luminance'
# Audio reaction: High frequencies physically tear the image outward
displace_glitch.par.weightx.expr = "op('snare_analyze')['chan1'] * 0.4"
displace_glitch.par.weighty.expr = "op('snare_analyze')['chan1'] * 0.4"

# =========================================================================
# 6. TEMPORAL FEEDBACK LOOP TOPs (Creates Y2K visual ghosting trails)
# =========================================================================
feedback_start = root.create(feedbackTOP, 'ghosting_feedback')
feedback_start.connect(displace_glitch)

feedback_level = root.create(levelTOP, 'feedback_opacity_mod')
feedback_level.connect(feedback_start)
# Audio reaction: High audio levels sustain the video trail transparency longer
feedback_level.par.opacity.expr = "0.85 + (op('snare_analyze')['chan1'] * 0.12)"

feedback_comp = root.create(compTOP, 'feedback_compositor')
feedback_comp.connect(displace_glitch, 0)
feedback_comp.connect(feedback_level, 1)
feedback_comp.par.operand = 'max'

feedback_start.par.targettop = './' + feedback_comp.name

# =========================================================================
# 7. POST PROCESSING & OUTPUT
# =========================================================================
final_out = root.create(outTOP, 'video_output_final')
final_out.connect(feedback_comp)

# Movie export bridge setup
movie_export = root.create(moviefileoutTOP, 'render_export_node')
movie_export.connect(final_out)
movie_export.par.audiofile.expr = "op('audio_source')"

print(f"Breakcore engine successfully compiled with {NUM_VIDEOS} inputs! Upload your media files directly to the generated source nodes.")
