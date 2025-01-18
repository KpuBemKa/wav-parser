from pathlib import Path
from abc import ABC, abstractmethod

class ReviewStrategy(ABC):
    @abstractmethod
    def handle_audio(self, audio_path: Path) -> None:
        pass

    @abstractmethod
    def handle_text(self, text_message: str) -> None:
        pass