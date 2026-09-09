from ai.parsing.audio_parser import (
    parse_audio,
)
from ai.parsing.csv_parser import (
    parse_csv,
)
from ai.parsing.pdf_parser import (
    parse_pdf,
)
from ai.parsing.text_parser import (
    parse_text,
)
from ai.parsing.xlsx_parser import (
    parse_xlsx,
)
from ai.parsing.models import (
    ParsedInputItem,
)


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".csv",
    ".xlsx",
    ".pdf",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
}


def parse_input(
    filename: str,
    file_bytes: bytes,
) -> list[ParsedInputItem]:

    lower_name = filename.lower()

    if lower_name.endswith(".txt"):

        text = file_bytes.decode(
            "utf-8",
            errors="replace",
        )

        return parse_text(
            text
        )

    if lower_name.endswith(".csv"):
        return parse_csv(
            file_bytes
        )

    if lower_name.endswith(".xlsx"):
        return parse_xlsx(
            file_bytes
        )

    if lower_name.endswith(".pdf"):
        return parse_pdf(
            file_bytes
        )

    if lower_name.endswith(
        (
            ".mp3",
            ".wav",
            ".m4a",
            ".aac",
        )
    ):
        return parse_audio(
            filename=filename,
            file_bytes=file_bytes,
        )

    raise ValueError(
        "Unsupported file type. "
        "Supported types: TXT, CSV, XLSX, PDF, "
        "MP3, WAV, M4A and AAC."
    )