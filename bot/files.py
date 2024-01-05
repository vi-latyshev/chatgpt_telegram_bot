import io
import PyPDF2
import tiktoken

from openai_utils import (
    OPENAI_COMPLETION_OPTIONS
)

"""
Inspired by https://github.com/father-bot/chatgpt_telegram_bot/compare/main...madiele:chatgpt_telegram_bot:main
"""

MAX_TOKENS_IN_STRING = OPENAI_COMPLETION_OPTIONS.get('max_tokens', 1000)

class FileTypeReader(object):
    def __init__(self):
        pass

    def is_mime_type(self, mime_type):
        raise NotImplementedError

    def to_strings(self, buf: io.BytesIO, encoding: tiktoken.Encoding) -> tuple[list, int]:
        raise NotImplementedError


class PlainTextReader(FileTypeReader):
    def __init__(self):
      super(PlainTextReader, self).__init__()

    def is_mime_type(self, mime_type):
        return (mime_type.startswith('text')
            or mime_type == 'application/json')

    def to_strings(self, buf: io.BytesIO, encoding: tiktoken.Encoding) -> tuple[list, int]:
        file_data = buf.read().decode()
        splitted_file_data = file_data.split()

        strings = []
        current_string = ""
        total_tokens = 0

        for word in splitted_file_data:
            current_string += word + " "

            tokens_in_string = len(encoding.encode(current_string))
            if tokens_in_string >= MAX_TOKENS_IN_STRING:
                strings.append(current_string.strip())
                total_tokens += tokens_in_string
                current_string = ""

        if current_string != "":
            tokens_in_string = len(encoding.encode(current_string))
            total_tokens += tokens_in_string
            strings.append(current_string.strip())

        return strings, total_tokens


class PdfReader(FileTypeReader):
    def __init__(self):
      super(PdfReader, self).__init__()

    def is_mime_type(self, mime_type):
        return mime_type == 'application/pdf'

    def to_strings(self, buf: io.BytesIO, encoding: tiktoken.Encoding) -> tuple[list, int]:
        pdf_reader = PyPDF2.PdfReader(buf)

        num_pages = len(pdf_reader.pages)
        total_tokens = 0

        strings = []

        for page_num in range(num_pages):
            page_obj = pdf_reader.pages[page_num]

            words = page_obj.extract_text().split()

            current_string = ""

            for word in words:
                current_string += word + " "

                tokens_in_string = len(encoding.encode(current_string))
                if tokens_in_string >= MAX_TOKENS_IN_STRING:
                    strings.append(current_string.strip())
                    total_tokens += tokens_in_string
                    current_string = ""

            if current_string != "":
                tokens_in_string = len(encoding.encode(current_string))
                total_tokens += tokens_in_string
                strings.append(current_string.strip())

        return strings, total_tokens


FILE_TYPES = (
    PdfReader(),
    PlainTextReader(),
)

def get_file_type_reader(mime_type: str) -> FileTypeReader:
    for file_type in FILE_TYPES:
        if file_type.is_mime_type(mime_type):
            return file_type

    raise ValueError(f'File extension (mime type) is not supported yet. Received Mime Type: {mime_type}')

def file_buffer_to_string_array(file_buf: io.BytesIO, mime_type: str, model: str) -> tuple[list, int]:
    encoding = tiktoken.encoding_for_model(model)

    file_type_reader = get_file_type_reader(mime_type)

    strings_in_file, total_tokens_in_file = file_type_reader.to_strings(file_buf, encoding)

    return strings_in_file, total_tokens_in_file
