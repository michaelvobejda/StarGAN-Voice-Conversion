from google.cloud import texttospeech
from google.cloud import translate
from pathlib import Path
import os
from tqdm import tqdm
import re
from pydub import AudioSegment
import io
from google.oauth2 import service_account

# Google Cloud Authentication
CLOUD_CREDS_PATH = Path('api_keys').joinpath('google_cloud.json')
assert CLOUD_CREDS_PATH.exists()
CLOUD_CREDS = service_account.Credentials.from_service_account_file(CLOUD_CREDS_PATH)

TTS_CLIENT = texttospeech.TextToSpeechClient(credentials=CLOUD_CREDS)
TRANS_CLIENT = translate.Client(credentials=CLOUD_CREDS)
VCTK_PATH = Path('VCTK-Corpus')
SRC_LANG = 'en'
DEST_LANG = 'de'

text_counts = {}


def get_synth_dir(person):
    synth_dir = VCTK_PATH.joinpath('synth_audio', DEST_LANG, person)
    os.makedirs(synth_dir, exist_ok=True)
    return synth_dir


def create_person_audio(person):
    text_path = VCTK_PATH.joinpath('txt', person)
    synth_audio_path = get_synth_dir(person)
    for txt_file in tqdm(list(os.listdir(text_path))):
        assert txt_file[-4:] == '.txt'
        with open(text_path.joinpath(txt_file), 'r') as f:
            text = f.read()
            text_counts[text] = text_counts.get(text, 0) + 1
            base_name = os.path.splitext(txt_file)[0]
            output_file = synth_audio_path.joinpath(base_name).with_suffix('.wav')
            tts(text, output_file)


def tts(text, output_file):
    if SRC_LANG != DEST_LANG:
        text = translate(text)

    synthesis_input = texttospeech.types.SynthesisInput(text=text)
    voice = texttospeech.types.VoiceSelectionParams(
        language_code=DEST_LANG,
        # Leaving gender as neutral for now. Could train
        # multiple models, one just for male-to-male and one for female-to-female.
        ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)
    response = TTS_CLIENT.synthesize_speech(synthesis_input, voice, audio_config)
    mp3_audio_content_to_wav(response.audio_content, output_file)


def mp3_audio_content_to_wav(audio_content, output_file):
    s = io.BytesIO(audio_content)
    AudioSegment.from_file(s).export(output_file, format='wav')


def get_all_people():
    # Arbitrarily choose the txt dir to iterate through.
    people = os.listdir(VCTK_PATH.joinpath('txt'))
    person_regex = re.compile(r'p\d\d\d')
    return sorted([person for person in people if person_regex.match(person)])


def translate(text):
    result = TRANS_CLIENT.translate(
        text, source_language=SRC_LANG, target_language=DEST_LANG)
    return result['translatedText']


def run():
    start = 0
    end = 4
    for person in tqdm(all_people[start:end]):
        print(person)
        create_person_audio(person)


all_people = get_all_people()

#create_person_audio('p225')
#run()

