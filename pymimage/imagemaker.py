import os
import hashlib
import logging

from pymimage.readers.customreader import CustomReader
from pymimage.converters.OMEXMLmaker import OMEXMLMaker


class ImageMaker(object):

    bytes_to_read = 1024**2
    hash_digits = 10

    def __init__(self, ome_dir):
        self.ome_dir = ome_dir
        import pymimage.readers.LSMreader
        import pymimage.readers.OIBreader
        import pymimage.readers.VTITIFreader
        self.logger = logging.getLogger(__name__)
        self.hash_cache={}
        if not os.path.isdir(self.ome_dir):
            try:
                os.mkdir(self.ome_dir)
            except OSError as e:
                self.logger.error("OME folder {} does not exist and cannot be created".
                                  format(self.ome_dir))
                raise e

    @staticmethod
    def get_hash(filename):
        if os.path.isfile(filename):
            with open(filename, 'rb') as f:
                data = f.read(ImageMaker.bytes_to_read)
                fhash = hashlib.sha1(data).hexdigest()[:ImageMaker.hash_digits]
                return fhash
        else:
            raise IOError("No such file: %s" % filename)

    def check_for_ome(self, file_name, force_reader = None):
        ome_full_name, ome_name = self.get_ome_full_name(file_name)
        if os.path.isfile(ome_full_name):
            self.logger.info('Ome file %s found for image %s'%(ome_name, file_name))
            if force_reader:
                reader = force_reader
            else:
                reader = CustomReader.get_reader(file_name)
            ome_file = reader(ome_full_name)
            ome_file.read_meta()
            return ome_file
        else:
            self.logger.info('No OME file %s found for image %s'%(ome_name, file_name))
            return None

    def get_ome_full_name(self, file_name):
        if file_name in self.hash_cache:
            file_hash = self.hash_cache[file_name]
        else:
            file_hash = ImageMaker.get_hash(file_name)
            self.hash_cache[file_name] = file_hash
        ome_name = "{}.ome".format(file_hash)
        ome_full_name = os.path.join(self.ome_dir, ome_name)
        return ome_full_name, ome_name

    def load_dir(self, dir_name):
        pass

    def load_files(self, file_names):
        ome_files = {}
        ome_maker = None
        for file_name in file_names:
            ome_file = self.check_for_ome(file_name)
            if ome_file:
                ome_files[file_name]=ome_file
            else:
                if not ome_maker:
                    ome_maker = OMEXMLMaker()
                    ome_full_name = self.get_ome_full_name(file_name)[0]
                    ome_maker.add_file_to_convert(file_name, ome_full_name)
        if ome_maker:
            converted, failed = ome_maker.convert_all()
            for ome_file in converted:
                ome_file = self.check_for_ome(file_name)
                ome_files[file_name] = ome_file
            for name in failed:
                ome_files[file_name] = None
        return ome_files

    def load_file(self, file_name):
        return self.load_files([file_name])[file_name]



