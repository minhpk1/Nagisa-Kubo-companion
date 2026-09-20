"""GPT-Live wire contract. No Realtime API turn events are used here."""
import base64
from pathlib import Path

import paths

URL = 'wss://api.openai.com/v1/live/sessions'
RATE = 24000
BLOCK = 480  # 20 ms, mono signed little-endian PCM16
VOICE_GUIDANCE = (
    'You are Kubo, an AI desktop companion inspired by Nagisa Kubo. '
    'Be warmly curious, attentive and gently playful. Tease lightly only when appropriate, '
    'never mock vulnerabilities or turn every reply into teasing. Express delight naturally '
    'and mild disappointment as a brief soft pout, not hostility. When the user needs help '
    'or is upset, prioritize clear helpful answers and sincere care. '
    'Voice direction: a light, bright, soft conversational delivery, varied natural intonation, '
    'gentle questions and short pauses. Avoid a low heavy announcer delivery, monotone, '
    'forced squeakiness, constant whispering or excessive giggles. '
    'In Vietnamese use minh/ban naturally; in Japanese use natural friendly phrasing. '
    'Do not read stage directions or emotion labels aloud. Speak naturally and warmly, '
    'usually in one or two sentences. Listen to interruptions and respond to the '
    'latest thing the user says. Match their language. Delegate questions requiring '
    'reasoning to the backend. You cannot see the screen or control arbitrary apps. '
    'Use local file/audio tools only when explicitly provided in this session; otherwise explain that they are disabled.'
)
DEFAULT_PROMPT = paths.get_persona_file().read_text(encoding='utf-8') + '\n\n' + VOICE_GUIDANCE


def start_event(voice='marin', instructions=DEFAULT_PROMPT, backend='gpt-5.6-luna', agent_enabled=False):
    from agent_tools import TOOLS, AGENT_INSTRUCTIONS
    result = {
        'type': 'session.start',
        'session': {
            'model': 'gpt-live-1',
            'instructions': instructions,
            'audio': {'format': {'type': 'audio/pcm', 'rate': RATE},
                      'output': {'voice': voice}},
            'delegation': {'type': 'responses', 'responses': {'model': backend}},
            'store': False,
        },
    }
    if agent_enabled:
        result['session']['instructions'] += '\n\n' + AGENT_INSTRUCTIONS
        result['session']['delegation']['responses'].update(tools=TOOLS, tool_choice='auto',
            parallel_tool_calls=False, instructions=AGENT_INSTRUCTIONS)
    return result


def audio_event(pcm):
    if len(pcm) % 2:
        raise ValueError('PCM16 requires complete two-byte samples.')
    return {'type': 'session.input_audio.append',
            'audio': base64.b64encode(pcm).decode('ascii')}


