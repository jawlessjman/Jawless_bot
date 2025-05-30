max_length = 10  # Maximum length of the audio queue

class audio:
    def __init__(self, url, _type: str, name: str):
        self.video : str = url
        self.type : str = _type
        self.name : str = name

class audio_queue:
    def __init__(self):
        self.queue = []
        self.current = None
        self.player = None
        self.loop = False
        self.channel = None  # Placeholder for the channel, if needed
        
    def reset(self):
        """Reset the audio queue."""
        self.queue = []
        self.current = None
        self.player = None
        self.loop = False
        
    def is_empty(self) -> bool:
        """Check if the audio queue is empty."""
        return len(self.queue) == 0
    
    def get_length(self) -> int:
        """Get the current length of the audio queue."""
        return len(self.queue)
        
    def add_audio(self, audio: audio) -> bool:
        """Add audio to the queue."""
        if len(self.queue) >= max_length:
            return False
        self.queue.append(audio)
        return True
    
    def get_next_audio(self) -> audio | None:
        """Get the next audio in the queue."""
        if self.queue:
            self.current = self.queue.pop(0)
            return self.current
        return None
    
    def pop_to_position(self, position: int) -> bool:
        """Pop audio from a specific position in the queue."""
        #pop everything before the position
        if 0 <= position < len(self.queue):
            for _ in range(position):
                if self.queue:
                    self.queue.pop(0)
            return True
        return False
    
    def pop_at_position(self, position: int) -> audio | None:
        """Pop audio at a specific position in the queue."""
        if 0 <= position < len(self.queue):
            return self.queue.pop(position)
        return None
