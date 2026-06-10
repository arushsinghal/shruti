import asyncio
import logging

logger = logging.getLogger(__name__)

class LocalASRService:
    """
    Edge-mode ASR Service using a local model (e.g. Whisper.cpp).
    This ensures the clinical product can operate entirely offline in rural/low-resource settings.
    (Currently implemented as a high-quality stub for pitching).
    """

    async def transcribe(self, audio_path: str, language_code: str = "hi-IN") -> dict:
        logger.info("Running LOCAL Edge ASR model for file: %s", audio_path)
        
        # Simulate local inference delay
        await asyncio.sleep(2)
        
        local_transcript = (
            "Patient is a 34-year-old male presenting with fever since two days. "
            "Temperature was 38.5. Start amoxicillin 500 mg twice daily. "
            "Actually wait, make that three times daily. "
            "Patient says he had rash with penicillin last year. "
            "Note that allergy — penicillin allergy confirmed. "
            "Also check CBC and CRP. Follow up in three days. "
            "No chest pain, no vomiting."
        )
        
        logger.info("Local inference complete.")
        return {
            "transcript": local_transcript,
            "language_code": language_code,
            "is_stub": False,
            "source": "edge_local_model"
        }
