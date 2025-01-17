import pathlib
import json

from collections.abc import Callable

from modules.ais.audio_transcriber import AudioTranscriber
from modules.ais.review_analizer import ReviewAnalizer


class BotStrategy:
    def __init__(self, send_message_func: Callable[[str], None]) -> None:
        self.__send_message_func = send_message_func

    def handle_audio(self, audio_path: pathlib.Path) -> None:
        # transcribed = AudioTranscriber().transcribe_audio(audio_path)

        # if transcribed is not None:
        review = ReviewAnalizer().summarize_review(
            " It was a great ambience and friendly stuff. The bruschetta was fresh and the truffle risotto was delicious. The grilled salmon was slightly overcooked and the service was a bit slow. We waited for the minute for the main courses. However, the tiramisu was outstanding. Thank you."
        )
        
        print(review.corrected_text)
        print(review.summary)
        
        for issue in review.issues:
            print(issue.description)
            
            for dep in issue.departments:
                print(dep.value, sep=", ")
