from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):

    def get_available_name(self, name):
        # If the filename already exists,
        #  remove it as if it was a true file system
        for path in (name, name+'_l', name+'_s'):
            if self.exists(path):
                self.delete(path)
        return name