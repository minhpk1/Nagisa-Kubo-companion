import unittest
from emotions import infer_emotion, conversation_emotion, ConversationExpressions

class EmotionTests(unittest.TestCase):
    def test_vietnamese_and_english(self):
        for text, expected in [('Mình rất vui', 'happy'), ('Tôi buồn', 'sad'),
                               ('Tức giận quá', 'angry'), ('Mình ngại', 'shy'),
                               ('Wow!', 'surprised'), ('Hello', 'neutral')]:
            self.assertEqual(infer_emotion(text), expected)

    def test_negation_and_word_boundaries(self):
        self.assertEqual(infer_emotion('không buồn'), 'neutral')
        self.assertEqual(infer_emotion('not sad'), 'neutral')
        self.assertEqual(infer_emotion('greatest'), 'neutral')

    def test_latest_emotion_wins(self):
        self.assertEqual(infer_emotion('Trước buồn nhưng giờ vui'), 'happy')

    def test_conversation_situations(self):
        for text, expected in [('Kubo dễ thương quá', 'shy'), ('Mình thi trượt rồi', 'sad'),
                               ('Hứ, đừng trêu mình nữa', 'angry'), ('Thật sao?', 'surprised'),
                               ('Mình làm được rồi!', 'happy'), ('Chào bạn!', 'happy'),
                               ('本当？', 'surprised'), ('嬉しいです', 'happy'), ('かわいいね', 'shy')]:
            with self.subTest(text=text):
                self.assertEqual(conversation_emotion(text, 'You'), expected)
        self.assertEqual(conversation_emotion('Kubo không đáng yêu', 'You'), 'neutral')
        self.assertEqual(conversation_emotion('Cô ấy rất dễ thương', 'You'), 'neutral')

    def test_streaming_hold_expiry_and_manual_reset(self):
        now = [0.0]
        tracker = ConversationExpressions(clock=lambda: now[0])
        self.assertEqual(tracker.feed('You', 'Kubo dễ '), 'neutral')
        self.assertEqual(tracker.feed('You', 'thương quá'), 'shy')
        now[0] = .5
        self.assertEqual(tracker.feed('Kubo', 'Bạn nói '), 'shy')
        self.assertEqual(tracker.feed('Kubo', 'thế à?'), 'shy')
        now[0] = 11
        self.assertEqual(tracker.current(), 'neutral')
        self.assertEqual(tracker.feed('You', 'Hôm nay thời tiết ra sao?'), 'neutral')
        tracker.feed('You', ' Wow!')
        tracker.reset()
        self.assertEqual(tracker.current(), 'neutral')

    def test_interleaved_fragments_do_not_destroy_each_other(self):
        tracker = ConversationExpressions(clock=lambda: 0)
        tracker.feed('You', 'Mình thi ')
        tracker.feed('Kubo', 'Mình đang nghe.')
        self.assertEqual(tracker.feed('You', 'trượt rồi'), 'sad')

if __name__ == '__main__':
    unittest.main()
