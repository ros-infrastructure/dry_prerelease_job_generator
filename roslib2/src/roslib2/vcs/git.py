import subprocess
import os
import vcs_base

class GITClient(vcs_base.VCSClientBase):
    def get_url(self):
        """
        @return: GIT URL of the directory path (output of git info command), or None if it cannot be determined
        """
        if self.detect_presence():
            output = subprocess.Popen(["git", "config",  "--get", "remote.origin.url"], cwd=self._path, stdout=subprocess.PIPE).communicate()[0]
            matches = [l for l in output.split('\n') if l.startswith('URL: ')]
            if matches:
                return matches[0][5:]
        return None

    def detect_presence(self):
        return self.path_exists() and os.path.isdir(os.path.join(self._path, '.git'))


    def checkout(self, url, version=''):
        if self.path_exists():
            print >>sys.stderr, "Error: cannnot checkout into existing directory"
            return False
            
        cmd = "git clone %s %s %s"%(version, url, self._path)
        if subprocess.check_call(cmd, shell=True) == 0:
            return True
        return False

    def update(self, version=''):
        if not self.detect_presence():
            return False
        cmd = "git pull %s %s %s"%(self._path, self.get_url(), version)
        if subprocess.check_call(cmd, shell=True) == 0:
            return True
        return False
        
    def get_vcs_type_name(self):
        return 'git'
