import os
import tempfile

from dotenv import load_dotenv
from google import genai

from ai.parsing.models import ParsedInputItem


load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

TRANSCRIBE_MODEL = os.getenv(
    "GEMINI_TRANSCRIBE_MODEL",
    "gemini-3.5-transcribe",
)


SUPPORTED_AUDIO = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
}


def get_extension(
    filename: str,
) -> str:

    lower_name = filename.lower()

    for extension in SUPPORTED_AUDIO:
        if lower_name.endswith(extension):
            return extension

    raise ValueError(
        "Unsupported audio format. "
        "Supported formats: MP3, WAV, M4A, AAC."
    )


def transcribe_audio(
    filename: str,
    file_bytes: bytes,
) -> str:

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    if not file_bytes:
        raise ValueError(
            "Audio file is empty."
        )

    extension = get_extension(
        filename
    )

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            temp_file.write(
                file_bytes
            )

            temp_path = (
                temp_file.name
            )

        print(
            "[VOICE] Uploading:",
            filename
        )

        print(
            "[VOICE] Size:",
            len(file_bytes),
            "bytes"
        )

        audio_file = (
            client.files.upload(
                file=temp_path
            )
        )

        print(
            "[VOICE] Gemini file uploaded"
        )

        interaction = (
            client.interactions.create(
                model=TRANSCRIBE_MODEL,
                input=[
                    {
                        "type": "audio",
                        "uri": audio_file.uri,
                        "mime_type": (
                            audio_file.mime_type
                        ),
                    }
                ],
                generation_config={
                    "transcription_config": {
                        "mode": "smart",
                        "language_codes": [],
                    }
                },
            )
        )

        transcript = (
            interaction.output_text
            or ""
        ).strip()

        if not transcript:
            raise RuntimeError(
                "No speech was detected "
                "in the audio file."
            )

        print(
            "[VOICE] Transcript:",
            transcript
        )

        return transcript

    finally:
        if (
            temp_path
            and os.path.exists(
                temp_path
            )
        ):
            os.remove(
                temp_path
            )


def parse_audio(
    filename: str,
    file_bytes: bytes,
) -> list[ParsedInputItem]:

    transcript = transcribe_audio(
        filename=filename,
        file_bytes=file_bytes,
    )

    return [
        ParsedInputItem(
            raw_text=transcript,
        )
    ]