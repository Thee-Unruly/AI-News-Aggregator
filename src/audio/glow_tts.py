import sys
import os
import torch
import time
import IPython
import json
import librosa  # Ensure librosa is imported

# Add the TTS repo to the system path
sys.path.append('TTS')

from TTS.utils.audio import AudioProcessor
from TTS.tts.utils.generic_utils import setup_model
from TTS.tts.utils.text.symbols import symbols, phonemes
from TTS.tts.utils.synthesis import synthesis
from TTS.tts.utils.io import load_checkpoint

def load_config(config_path):
    """Load configuration from a JSON file with UTF-8 encoding."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def interpolate_vocoder_input(scale_factor, spec):
    """Interpolation to tolerate the sampling rate difference
    between TTS model and vocoder."""
    print(" > before interpolation :", spec.shape)
    spec = torch.tensor(spec).unsqueeze(0).unsqueeze(0)
    spec = torch.nn.functional.interpolate(spec, scale_factor=scale_factor, mode='bilinear').squeeze(0)
    print(" > after interpolation :", spec.shape)
    return spec

def tts(model, text, CONFIG, use_cuda, ap, use_gl, figures=True):
    t_1 = time.time()
    # Run TTS
    target_sr = CONFIG['audio']['sample_rate']
    waveform, alignment, mel_spec, mel_postnet_spec, stop_tokens, inputs = \
        synthesis(model,
                  text,
                  CONFIG,
                  use_cuda,
                  ap,
                  speaker_id,
                  None,
                  False,
                  CONFIG['enable_eos_bos_chars'],
                  use_gl)
    
    # Run vocoder
    mel_postnet_spec = ap._denormalize(mel_postnet_spec.T).T
    if not use_gl:
        target_sr = VOCODER_CONFIG['audio']['sample_rate']
        vocoder_input = ap_vocoder._normalize(mel_postnet_spec.T)
        if scale_factor[1] != 1:
            vocoder_input = interpolate_vocoder_input(scale_factor, vocoder_input)
        else:
            vocoder_input = torch.tensor(vocoder_input).unsqueeze(0)
        waveform = vocoder_model.inference(vocoder_input)

    # Format output
    if use_cuda and not use_gl:
        waveform = waveform.cpu()
    if not use_gl:
        waveform = waveform.numpy()
    waveform = waveform.squeeze()

    # Compute run-time performance
    rtf = (time.time() - t_1) / (len(waveform) / ap.sample_rate)
    tps = (time.time() - t_1) / len(waveform)
    print(waveform.shape)
    print(" > Run-time: {}".format(time.time() - t_1))
    print(" > Real-time factor: {}".format(rtf))
    print(" > Time per step: {}".format(tps))

    # Display audio
    IPython.display.display(IPython.display.Audio(waveform, rate=target_sr))
    return alignment, mel_postnet_spec, stop_tokens, waveform

# Runtime settings
use_cuda = True

# Model paths
TTS_MODEL = "tts_model.pth.tar"
TTS_CONFIG = "config.json"
VOCODER_MODEL = "vocoder_model.pth.tar"
VOCODER_CONFIG = "config_vocoder.json"

# Load configs
TTS_CONFIG = load_config(TTS_CONFIG)
VOCODER_CONFIG = load_config(VOCODER_CONFIG)

# Set default values for audio parameters if None
audio_config = TTS_CONFIG['audio']
if audio_config.get('frame_length_ms') is None:
    audio_config['frame_length_ms'] = 50  # Set an appropriate value
if audio_config.get('frame_shift_ms') is None:
    audio_config['frame_shift_ms'] = 12.5  # Set an appropriate value

# Load the audio processor
class CustomAudioProcessor(AudioProcessor):
    def _build_mel_basis(self):
        return librosa.filters.mel(
            sr=self.sample_rate,
            n_fft=self.fft_size,
            n_mels=self.num_mels,
            fmin=self.mel_fmin,
            fmax=self.mel_fmax
        )

# Create an instance of the modified audio processor
ap = CustomAudioProcessor(**audio_config)

from TTS.tts.utils.text.symbols import make_symbols

# LOAD TTS MODEL
speakers = []
speaker_id = None

if 'characters' in TTS_CONFIG.keys():
    symbols, phonemes = make_symbols(**TTS_CONFIG['characters'])

# Load the model
num_chars = len(phonemes) if TTS_CONFIG['use_phonemes'] else len(symbols)
model = setup_model(num_chars, len(speakers), TTS_CONFIG)

# Load model state
model, _ = load_checkpoint(model, TTS_MODEL, use_cuda=use_cuda)
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
if use_cuda:
    vocoder_model.cuda()
vocoder_model.eval()

# Model settings
model.length_scale = 1.0  # Set speed of the speech
model.noise_scale = 0.33  # Set speech variation

# Input sentence for TTS
sentence = "Bill got in the habit of asking himself “Is that thought true?” and if he wasn’t absolutely certain it was, he just let it go."

# Run TTS and get the results
align, spec, stop_tokens, wav = tts(model, sentence, TTS_CONFIG, use_cuda, ap, use_gl=False, figures=True)
