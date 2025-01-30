from dataclasses import dataclass
from typing import Optional, Union
import numpy as np

@dataclass
class VoiceMessage:
    """Class representing a voice message with audio data."""
    audio_data: Union[bytes, np.ndarray]
    sample_rate: int
    text_content: Optional[str] = None
    duration: Optional[float] = None
    format: str = "wav"

    def __post_init__(self):
        if isinstance(self.audio_data, np.ndarray):
            self.duration = len(self.audio_data) / self.sample_rate
