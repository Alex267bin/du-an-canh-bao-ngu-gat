import numpy as np

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

_audio_enabled = True
_sound = None
_channel = None


def set_audio_enabled(enabled: bool):
    global _audio_enabled
    _audio_enabled = enabled
    if not enabled:
        stop_alarm()


def _ensure_mixer():
    if not _audio_enabled or not PYGAME_AVAILABLE:
        return False

    if pygame.mixer.get_init() is None:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
        except Exception:
            return False
    return True


def _generate_beep(frequency=1000, duration=0.4, volume=0.5):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(2 * np.pi * frequency * t)
    audio = (wave * 32767 * volume).astype(np.int16)
    return pygame.sndarray.make_sound(audio)


def play_alarm():
    global _sound, _channel
    if not _audio_enabled or not PYGAME_AVAILABLE:
        return

    if not _ensure_mixer():
        return

    if _sound is None:
        _sound = _generate_beep()

    if _channel is None or not _channel.get_busy():
        _channel = _sound.play()


def stop_alarm():
    global _channel
    if not _audio_enabled or not PYGAME_AVAILABLE:
        return

    if _channel is not None:
        _channel.stop()
        _channel = None
