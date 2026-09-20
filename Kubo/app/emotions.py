"""Small local text heuristic, not voice sentiment recognition."""
import re
import unicodedata
import time

EMOTIONS = {'neutral': 'Bình thường', 'happy': 'Vui vẻ', 'sad': 'Buồn',
            'angry': 'Giận dỗi', 'shy': 'Ngại ngùng', 'surprised': 'Ngạc nhiên'}

def infer_emotion(text):
    text = unicodedata.normalize('NFC', text).casefold()
    groups = {
        'sad': ('buồn', 'khóc', 'cô đơn', 'mệt mỏi', 'sad', 'lonely'),
        'angry': ('tức giận', 'bực', 'giận', 'angry', 'furious'),
        'shy': ('ngại', 'xấu hổ', 'yêu bạn', 'thích bạn', 'shy', 'love you'),
        'surprised': ('wow', 'bất ngờ', 'ngạc nhiên', 'surprised'),
        'happy': ('vui', 'tuyệt', 'hạnh phúc', 'cảm ơn', 'happy', 'great', 'thank you'),
    }
    matches = []
    for emotion, words in groups.items():
        for word in words:
            for match in re.finditer(r'(?<!\w)' + re.escape(word) + r'(?!\w)', text):
                prefix = text[max(0, match.start()-18):match.start()]
                if not re.search(r'(không|chẳng|chưa|not|never)\s+(?:còn\s+|rất\s+)?$', prefix):
                    matches.append((match.start(), emotion))
    return max(matches)[1] if matches else 'neutral'


def conversation_emotion(text, speaker='Kubo'):
    """Local, explainable conversation cues; not a general semantic classifier."""
    text = unicodedata.normalize('NFC', text).casefold()
    groups = {
        'happy': ('chúc mừng', 'làm được rồi', 'thành công rồi', 'đậu rồi', 'đỗ rồi',
                  'haha', 'hihi', 'hay quá', 'giỏi quá', 'mừng quá', 'thích quá',
                  'rất vui', 'chào bạn', 'được chứ', 'tất nhiên rồi', 'hehe', 'こんにちは',
                  '嬉しい', '楽しい', 'やった', 'ありがとう', 'おめでとう'),
        'sad': ('thi trượt', 'bị điểm kém', 'mất việc', 'chia tay', 'không ai quan tâm',
                'không ổn', 'kiệt sức', 'thất vọng', 'xin lỗi', 'tệ quá', 'đau lòng',
                'mình ở đây với bạn', 'mình sẽ lắng nghe', '悲しい', '寂しい', 'つらい', 'ごめん'),
        'angry': ('đồ ngốc', 'đáng ghét', 'đừng trêu', 'trêu mình', 'chọc mình',
                  'dỗi đấy', 'dỗi rồi', 'hứ', 'hừm', 'もうっ', 'ずるい', 'いじわる'),
        'shy': ('dễ thương', 'đáng yêu', 'xinh quá', 'xinh lắm', 'thích cậu', 'yêu cậu',
                'thích kubo', 'yêu kubo', 'đỏ mặt', 'ngượng', 'khen mình',
                'かわいい', '可愛い', '照れる', '恥ずかしい', '大好き'),
        'surprised': ('thật sao', 'thật hả', 'không thể tin', 'không ngờ', 'trúng số',
                      'ôi trời', 'ơ kìa', 'えっ', '本当', 'びっくり', 'まさか'),
    }
    matches = []
    for emotion, phrases in groups.items():
        for phrase in phrases:
            # Japanese has no word-separating spaces.
            pattern = re.escape(phrase) if re.search(r'[\u3040-\u30ff\u3400-\u9fff]', phrase) else r'(?<!\w)' + re.escape(phrase) + r'(?!\w)'
            for match in re.finditer(pattern, text):
                prefix = text[max(0, match.start()-24):match.start()]
                if re.search(r'(không|chẳng|chưa|not|never)\s+(?:còn\s+|rất\s+)?$', prefix):
                    continue
                if emotion == 'shy' and speaker in ('You', 'Bạn'):
                    # A compliment about somebody else should not make Kubo blush.
                    if re.search(r'(cô ấy|anh ấy|người khác|bạn gái tôi|cô bạn)\s*(?:rất\s+)?$', prefix):
                        continue
                matches.append((match.start(), emotion))
    return max(matches)[1] if matches else infer_emotion(text)


class ConversationExpressions:
    """Keep separate streaming transcripts and hold reactions across neutral fragments."""
    def __init__(self, clock=time.monotonic, hold=10):
        self.clock, self.hold = clock, hold
        self.reset()

    def reset(self):
        self.buffers = {}
        self.last_seen = {}
        self.last_speaker = None
        self.emotion = 'neutral'
        self.expires = 0

    def feed(self, speaker, delta):
        if not isinstance(delta, str) or not delta:
            return self.current()
        now = self.clock()
        # Same-speaker turns separated by a pause do not inherit old keywords.
        if now-self.last_seen.get(speaker, -100) > 3:
            self.buffers[speaker] = ''
        self.buffers[speaker] = (self.buffers.get(speaker, '') + delta)[-1200:]
        self.last_seen[speaker] = now
        self.last_speaker = speaker
        detected = conversation_emotion(self.buffers[speaker], speaker)
        if detected != 'neutral':
            self.emotion = detected
            self.expires = now+self.hold
        return self.current()

    def current(self):
        if self.clock() >= self.expires:
            self.emotion = 'neutral'
        return self.emotion
