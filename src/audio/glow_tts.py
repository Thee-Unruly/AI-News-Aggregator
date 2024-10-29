import sys
import os
import torch
import json
import librosa  # Ensure librosa is imported
from TTS.utils.audio import AudioProcessor
from TTS.tts.utils.generic_utils import setup_model
from TTS.tts.utils.text.symbols import symbols, phonemes
from TTS.tts.utils.synthesis import synthesis
from TTS.tts.utils.io import load_checkpoint
from TTS.tts.utils.text.symbols import make_symbols

# Add the TTS repo to the system path
sys.path.append('TTS')

def load_config(config_path):
    """Load JSON configuration from the specified path with UTF-8 encoding."""
    with open(config_path, 'r', encoding='utf-8') as config_file:
        return json.load(config_file)


# Model paths
TTS_MODEL = "tts_model.pth.tar"
TTS_CONFIG_PATH = r"C:\Users\ibrahim.fadhili\Desktop\AI AGGREGATOR\config.json"
VOCODER_MODEL = "vocoder_model.pth.tar"
VOCODER_CONFIG_PATH = r"C:\Users\ibrahim.fadhili\Desktop\AI AGGREGATOR\config_vocoder.json"

# Load TTS and Vocoder configs
TTS_CONFIG = load_config(TTS_CONFIG_PATH)
VOCODER_CONFIG = load_config(VOCODER_CONFIG_PATH)

# Ensure your config has the necessary fields
c = {
    'model': TTS_CONFIG['model'],
    'audio': TTS_CONFIG['audio'],
    'run_name': 'example_run',
    'run_description': 'An example run for TTS model',
    'num_speakers': TTS_CONFIG.get('num_speakers', 1),
    'hidden_channels_encoder': TTS_CONFIG.get('hidden_channels_encoder', 128),
    'hidden_channels_decoder': TTS_CONFIG.get('hidden_channels_decoder', 128),
    'hidden_channels_duration_predictor': TTS_CONFIG.get('hidden_channels_duration_predictor', 128),
    'characters': TTS_CONFIG['characters']
}

# Set default values for audio parameters if None
audio_config = TTS_CONFIG['audio']
audio_config.setdefault('frame_length_ms', 50)  # Set an appropriate value
audio_config.setdefault('frame_shift_ms', 12.5)  # Set an appropriate value

# Create an instance of the modified audio processor
class CustomAudioProcessor(AudioProcessor):
    def _build_mel_basis(self):
        return librosa.filters.mel(
            sr=self.sample_rate,
            n_fft=self.fft_size,
            n_mels=self.num_mels,
            fmin=self.mel_fmin,
            fmax=self.mel_fmax
        )

# Create an instance of the audio processor
ap = CustomAudioProcessor(**audio_config)

# Load TTS model
speakers = []
speaker_id = None

# Check for 'characters' in the TTS configuration
if 'characters' in TTS_CONFIG:
    symbols, phonemes = make_symbols(**TTS_CONFIG['characters'])  # Ensure you're accessing TTS_CONFIG correctly

# Load the model
num_chars = len(phonemes) if TTS_CONFIG['use_phonemes'] else len(symbols)  # Use correct indexing
model_info = setup_model(num_chars, len(speakers), TTS_CONFIG)

# Check the model output
model = model_info.get('model') if isinstance(model_info, dict) else model_info

# Ensure the model is not None
if model is None:
    raise ValueError("Model could not be loaded. Please check your configuration.")

# Load model state
model, _ = load_checkpoint(model, TTS_MODEL, use_cuda=torch.cuda.is_available())
model.eval()
model.store_inverse()

from TTS.vocoder.utils.generic_utils import setup_generator

# LOAD VOCODER MODEL
vocoder_model = setup_generator(VOCODER_CONFIG)
vocoder_model.load_state_dict(torch.load(VOCODER_MODEL, map_location="cpu")["model"])
vocoder_model.remove_weight_norm()
vocoder_model.inference_padding = 0

# Scale factor for sampling rate difference
scale_factor = [1, VOCODER_CONFIG['audio']['sample_rate'] / ap.sample_rate]
print(f"scale_factor: {scale_factor}")

ap_vocoder = AudioProcessor(**VOCODER_CONFIG['audio'])    
if torch.cuda.is_available():
    vocoder_model.cuda()
vocoder_model.eval()

# Model settings
model.length_scale = 1.0  # Set speed of the speech
model.noise_scale = 0.33  # Set speech variation

# Input sentence for TTS
sentence = "Bill got in the habit of asking himself 'Is that thought true?' and if he wasn’t absolutely certain it was, he just let it go."

# Run TTS and get the results
align, spec, stop_tokens, wav = synthesis(model, sentence, TTS_CONFIG, use_cuda=True, ap=ap, use_gl=False)

# Optionally save or play the output wave file here
