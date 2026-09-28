import os
import subprocess
import numpy as np
from scipy.io import wavfile
import imageio_ffmpeg

def generate_lofi_audio(output_wav_path, duration=50.0):
    sample_rate = 44100
    bpm = 84.0
    beat_dur = 60.0 / bpm
    num_samples = int(sample_rate * duration)

    chords = [
        [174.61, 220.00, 261.63, 329.63], # Fmaj7
        [164.81, 196.00, 246.94, 293.66], # Em7
        [146.83, 174.61, 220.00, 261.63], # Dm7
        [130.81, 164.81, 196.00, 246.94]  # Cmaj7
    ]
    measure_dur = beat_dur * 4.0

    chord_signal = np.zeros(num_samples)
    for i in range(int(duration / measure_dur) + 1):
        chord = chords[i % len(chords)]
        start_sample = int(i * measure_dur * sample_rate)
        end_sample = min(int((i + 1) * measure_dur * sample_rate), num_samples)
        if start_sample >= num_samples:
            break
        
        length = end_sample - start_sample
        t_chunk = np.linspace(0, length / sample_rate, length, endpoint=False)
        
        env = np.ones(length)
        attack = int(0.08 * sample_rate)
        decay = int(0.15 * sample_rate)
        if length > attack:
            env[:attack] = np.linspace(0, 1, attack)
        if length > decay:
            env[-decay:] = np.linspace(1, 0, decay)
            
        chord_wave = np.zeros(length)
        for freq in chord:
            wave = (0.65 * np.sin(2 * np.pi * freq * t_chunk) + 
                    0.25 * np.sin(2 * np.pi * freq * 2 * t_chunk) + 
                    0.10 * np.sin(2 * np.pi * freq * 3 * t_chunk))
            chord_wave += wave
            
        chord_signal[start_sample:end_sample] += chord_wave * env * 0.16

    bass_signal = np.zeros(num_samples)
    bass_roots = [174.61/2, 164.81/2, 146.83/2, 130.81/2]
    for i in range(int(duration / (beat_dur * 2)) + 1):
        root_freq = bass_roots[(i // 2) % len(bass_roots)]
        start_sample = int(i * beat_dur * 2 * sample_rate)
        length = int(beat_dur * 1.5 * sample_rate)
        end_sample = min(start_sample + length, num_samples)
        if start_sample >= num_samples:
            break
            
        act_len = end_sample - start_sample
        t_b = np.linspace(0, act_len / sample_rate, act_len, endpoint=False)
        env_b = np.exp(-t_b * 3.0)
        bass_wave = np.sin(2 * np.pi * root_freq * t_b) + 0.3 * np.sin(2 * np.pi * root_freq * 2 * t_b)
        bass_signal[start_sample:end_sample] += bass_wave * env_b * 0.25

    kick_signal = np.zeros(num_samples)
    snare_signal = np.zeros(num_samples)
    hihat_signal = np.zeros(num_samples)

    num_beats = int(duration / beat_dur) + 1

    for b in range(num_beats):
        b_start = int(b * beat_dur * sample_rate)
        bar_pos = b % 4
        
        if bar_pos in [0, 2]:
            k_len = int(0.2 * sample_rate)
            k_end = min(b_start + k_len, num_samples)
            act_k = k_end - b_start
            if act_k > 0:
                t_k = np.linspace(0, act_k / sample_rate, act_k, endpoint=False)
                freq_sweep = 120.0 * np.exp(-t_k * 30.0) + 40.0
                k_env = np.exp(-t_k * 15.0)
                kick_signal[b_start:k_end] += np.sin(2 * np.pi * freq_sweep * t_k) * k_env * 0.4
                
        if bar_pos in [1, 3]:
            s_len = int(0.18 * sample_rate)
            s_end = min(b_start + s_len, num_samples)
            act_s = s_end - b_start
            if act_s > 0:
                t_s = np.linspace(0, act_s / sample_rate, act_s, endpoint=False)
                noise = np.random.uniform(-1, 1, act_s)
                s_env = np.exp(-t_s * 25.0)
                tone = np.sin(2 * np.pi * 180.0 * t_s) * np.exp(-t_s * 40.0)
                snare_signal[b_start:s_end] += (noise * 0.7 + tone * 0.3) * s_env * 0.22
                
        for sub in [0, 0.5]:
            h_start = int((b + sub) * beat_dur * sample_rate)
            h_len = int(0.06 * sample_rate)
            h_end = min(h_start + h_len, num_samples)
            act_h = h_end - h_start
            if act_h > 0 and h_start < num_samples:
                t_h = np.linspace(0, act_h / sample_rate, act_h, endpoint=False)
                h_noise = np.random.uniform(-1, 1, act_h)
                h_env = np.exp(-t_h * 60.0)
                hihat_signal[h_start:h_end] += h_noise * h_env * (0.08 if sub == 0 else 0.05)

    np.random.seed(42)
    crackle = np.random.normal(0, 0.015, num_samples)
    crackle_clicks = (np.random.rand(num_samples) > 0.9995).astype(float) * np.random.uniform(0.05, 0.15, num_samples)
    vinyl_ambience = (crackle + crackle_clicks) * 0.15

    mixed_audio = chord_signal + bass_signal + kick_signal + snare_signal + hihat_signal + vinyl_ambience
    max_val = np.max(np.abs(mixed_audio))
    if max_val > 0:
        mixed_audio = mixed_audio / max_val * 0.85

    audio_int16 = (mixed_audio * 32767).astype(np.int16)
    wavfile.write(output_wav_path, sample_rate, audio_int16)
    print(f"Lo-fi audio track generated: {output_wav_path}")

def merge_audio_video():
    artifacts_dir = "/config/.gemini/antigravity/brain/a82cade4-c937-4efe-ad10-78629e6db2f2"
    video_path = os.path.join(artifacts_dir, "demo_recording.webm")
    wav_path = "/tmp/lofi_beat.wav"
    output_video_path = os.path.join(artifacts_dir, "demo_with_lofi.webm")
    
    generate_lofi_audio(wav_path, duration=50.0)
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    # Merge video and audio into output webm with opus audio codec
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", video_path,
        "-i", wav_path,
        "-c:v", "copy",
        "-c:a", "libopus",
        "-b:a", "128k",
        "-shortest",
        output_video_path
    ]
    
    print("Muxing video and audio with ffmpeg...")
    subprocess.run(cmd, check=True)
    print(f"Created demo with lo-fi music: {output_video_path}")
    
    # Overwrite main demo_recording.webm so it displays in walkthrough
    os.system(f"cp '{output_video_path}' '{video_path}'")
    print(f"Updated main demo artifact: {video_path} (size: {os.path.getsize(video_path)} bytes)")

if __name__ == "__main__":
    merge_audio_video()
