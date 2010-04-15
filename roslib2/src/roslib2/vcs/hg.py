import subprocess
import os
import vcs_base

class HGClient(vcs_base.VCSClientBase):
    def get_url(self):
        """
        @return: HG URL of the directory path (output of git info command), or None if it cannot be determined
        """
        if self.detect_presence():
            output = subprocess.Popen(["hg", "paths", "default"], cwd=self._path, stdout=subprocess.PIPE).communicate()[0]
            return output.rstrip()
        return None

    def detect_presence(self):
        return self.path_exists() and os.path.isdir(os.path.join(self._path, '.hg'))


    def checkout(self, url, version=''):
        if self.path_exists():
            print >>sys.stderr, "Error: cannnot checkout into existing directory"
            return False
            
        cmd = "hg clone %s %s"%(url, self._path)
        if not subprocess.check_call(cmd, shell=True) == 0:
            return False
        if version != '':
            cmd = "hg checkout -r %s"%(version)
            if not subprocess.check_call(cmd, cwd=self._path, shell=True) == 0:
                return False
        ## this would be the branching (like the git client does it), but it's not standard practice with hg
        ## (according to hg help branch)
        #cmd = "hg branch rosinstall"
        #if not subprocess.check_call(cmd, cwd=self._path, shell=True) == 0:
        #    return False
        return True

    def update(self, version=''):
        if not self.detect_presence():
            return False
        cmd = "hg pull"
        if not subprocess.check_call(cmd, cwd=self._path, shell=True) == 0:
            return False
        cmd = "hg checkout %s"%version
        if not subprocess.check_call(cmd, cwd=self._path, shell=True) == 0:
            return False
        return True
        
    def get_vcs_type_name(self):
        return 'hg'

    def get_version(self):
        output = subprocess.Popen(['hg', 'identify', "-i", self._path], stdout=subprocess.PIPE).communicate()[0]
        return output.strip()
