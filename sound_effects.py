import pygame
import numpy as np
import math

class ChimeSynthesizer:
    """Generates sweet, harmonic procedural chime audio buffers for flower blooms."""
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.enabled = False
        self.sounds = []
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=512)
            self.enabled = True
            self._generate_pentatonic_scale()
        except Exception as e:
            print(f"[SoundSynth] Audio initialization skipped or unavailable: {e}")
            self.enabled = False

    def _generate_pentatonic_scale(self):
        """Creates pentatonic chime notes (C5, D5, E5, G5, A5, C6)."""
        frequencies = [523.25, 587.33, 659.25, 783.99, 880.00, 1046.50]
        
        for freq in frequencies:
            sound = self._synthesize_chime(freq, duration=0.4)
            if sound:
                self.sounds.append(sound)

    def _synthesize_chime(self, frequency, duration=0.4):
        """Synthesizes a bell/chime sound using sine waves with exponential decay and overtones."""
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        # Fundamental frequency + harmonic overtones for metallic bell shimmer
        wave = 0.6 * np.sin(2 * np.pi * frequency * t)
        wave += 0.25 * np.sin(2 * np.pi * frequency * 2.0 * t)
        wave += 0.15 * np.sin(2 * np.pi * frequency * 3.01 * t)
        wave += 0.10 * np.sin(2 * np.pi * frequency * 4.12 * t)
        
        # Exponential volume envelope (percussive strike + smooth decay)
        envelope = np.exp(-6.0 * t)
        sound_data = wave * envelope
        
        # Normalize and convert to 16-bit signed stereo integers
        sound_data = np.clip(sound_data, -1.0, 1.0)
        stereo_data = np.zeros((num_samples, 2), dtype=np.int16)
        int_data = (sound_data * 32767).astype(np.int16)
        stereo_data[:, 0] = int_data
        stereo_data[:, 1] = int_data
        
        try:
            return pygame.sndarray.make_sound(stereo_data)
        except Exception:
            return None

    def play_chime(self, note_index=None):
        """Plays a chime sound from the scale."""
        if not self.enabled or not self.sounds:
            return
        
        try:
            if note_index is None:
                sound = np.random.choice(self.sounds)
            else:
                idx = note_index % len(self.sounds)
                sound = self.sounds[idx]
            
            sound.set_volume(0.3)
            sound.play()
        except Exception:
            pass
