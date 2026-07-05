import os
import uuid
import edge_tts

class TTSService:
    @staticmethod
    async def synthesize(text: str, output_dir: str = "src/static/audio") -> str:
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate a unique file name
            filename = f"reply_{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(output_dir, filename)
            
            # Use AvaNeural for a high quality, clear conversational voice
            communicate = edge_tts.Communicate(text, "en-US-AvaNeural")
            await communicate.save(filepath)
            
            # Return relative path for web usage
            return f"/static/audio/{filename}"
        except Exception as e:
            print(f"TTS synthesis error: {e}")
            return ""
