import os

class VCSClientBase:
    def __init__(self, path):
        self._path = path
        
    def path_exists(self):
        return os.path.exists(self._path)
        
    def get_path(self):
        return self._path

    def get_url(self):
        """
        @return: The source control url for the path
        @rtype: str
        """
        raise NotImplementedError, "Base class get_url method must be overridden"

    def get_version(self):
        raise NotImplementedError, "Base class get_version method must be overridden"

    def checkout(self, url, version):
        raise NotImplementedError, "Base class checkout method must be overridden"

    def update(self, version):
        raise NotImplementedError, "Base class update method must be overridden"
    

    def detect_presence(self):
        """For auto detection"""
        raise NotImplementedError, "Base class detect_presence method must be overridden"

    def get_vcs_type_name(self):
        """ used when auto detected """
        raise NotImplementedError, "Base class get_vcs_type_name method must be overridden"
