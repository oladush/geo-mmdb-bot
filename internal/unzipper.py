import os.path
import shutil
import subprocess
import zipfile
import patoolib
from io import BytesIO

class Zip:
    @staticmethod
    def unzip(raw_zip):
        extracted_files = {}
        with zipfile.ZipFile(BytesIO(raw_zip)) as zip_file:
            for file_info in zip_file.infolist():
                file_name = file_info.filename
                extracted_bytes = zip_file.read(file_name)
                extracted_files[file_name] = extracted_bytes
        return extracted_files


class SevenZip:
    @staticmethod
    def is_ready(path_to_archive):
        return bool(SevenZip.get_first(path_to_archive))

    @staticmethod
    def unzip(path_to_archive):
        first = SevenZip.get_first(path_to_archive)

        if not first:
            return None

        path_to_first = os.path.join(path_to_archive, first)
        path_to_unpack = os.path.join(path_to_archive, 'unpacked')

        try:
            os.makedirs(path_to_unpack)
        except FileExistsError:
            shutil.rmtree(path_to_unpack)
            os.makedirs(path_to_unpack)

        try:
            patoolib.extract_archive(path_to_first, outdir=path_to_unpack)
        except patoolib.util.PatoolError:
            result = subprocess.run(f'7z x {path_to_first} "-o{path_to_unpack}" -y',
                shell=True, capture_output=True, text=True)

        extracted_files = {}

        if SevenZip.is_unpacked(path_to_unpack):
            for file in os.listdir(path_to_unpack):
                path_to_file = os.path.join(path_to_unpack, file)
                with open(path_to_file, 'rb') as rf:
                    extracted_files[file] = rf.read()

        return extracted_files

    @staticmethod
    def is_unpacked(directory):
        return os.path.exists(directory) \
            and any(os.listdir(directory))

    @staticmethod
    def get_first(directory):
        for file in os.listdir(directory):
            if file.endswith('.001') or file.endswith('.7z'):
                return file
        return None


