import io
class HGClientTestSetups(unittest.TestCase):
        from vcstools.hg import HgClient
        self.directories = dict(setUp=directory)
        remote_path = os.path.join(directory, "remote")
        os.makedirs(remote_path)

        # create a "remote" repo
        subprocess.check_call(["hg", "init"], cwd=remote_path)
        subprocess.check_call(["touch", "fixed.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "add", "fixed.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "commit", "-m", "initial"], cwd=remote_path)
        subprocess.check_call(["hg", "tag", "test_tag"], cwd=remote_path)
        
        po = subprocess.Popen(["hg", "log", "--template", "'{node|short}'", "-l1"], cwd=remote_path, stdout=subprocess.PIPE)
        self.readonly_version_init = po.stdout.read().rstrip("'").lstrip("'")
        
        # files to be modified in "local" repo
        subprocess.check_call(["touch", "modified.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "modified-fs.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "add", "modified.txt", "modified-fs.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "commit", "-m", "initial"], cwd=remote_path)
        po = subprocess.Popen(["hg", "log", "--template", "'{node|short}'", "-l1"], cwd=remote_path, stdout=subprocess.PIPE)
        self.readonly_version_second = po.stdout.read().rstrip("'").lstrip("'")
        
        subprocess.check_call(["touch", "deleted.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "deleted-fs.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "add", "deleted.txt", "deleted-fs.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "commit", "-m", "modified"], cwd=remote_path)
        po = subprocess.Popen(["hg", "log", "--template", "'{node|short}'", "-l1"], cwd=remote_path, stdout=subprocess.PIPE)
        self.readonly_version = po.stdout.read().rstrip("'").lstrip("'")

        self.readonly_url = remote_path
        
        client = HgClient(self.readonly_path)
        self.assertTrue(client.checkout(remote_path, self.readonly_version))
class HGClientTest(HGClientTestSetups):
    def test_get_url_by_reading(self):
        from vcstools.hg import HgClient
        client = HgClient(self.readonly_path)
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEqual(client.get_url(), self.readonly_url)
        self.assertEqual(client.get_version(), self.readonly_version)
        from vcstools.hg import HgClient
        client = HgClient(local_path)
        self.assertEqual(client.get_vcs_type_name(), 'hg')
        from vcstools.hg import HgClient
        url = self.readonly_url
        client = HgClient(local_path)
        self.assertFalse(client.path_exists())
        self.assertFalse(client.detect_presence())
        self.assertFalse(client.detect_presence())
        self.assertTrue(client.checkout(url))
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEqual(client.get_path(), local_path)
        self.assertEqual(client.get_url(), url)
        from vcstools.hg import HgClient
        url = self.readonly_url
        client = HgClient(local_path)
        self.assertFalse(client.path_exists())
        self.assertFalse(client.detect_presence())
        self.assertFalse(client.detect_presence())
        self.assertTrue(client.checkout(url))
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEqual(client.get_path(), local_path)
        self.assertEqual(client.get_url(), url)
        from vcstools.hg import HgClient
        url = self.readonly_url
        version = self.readonly_version
        client = HgClient(local_path)
        self.assertFalse(client.path_exists())
        self.assertFalse(client.detect_presence())
        self.assertFalse(client.detect_presence())
        self.assertTrue(client.checkout(url, version))
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEqual(client.get_path(), local_path)
        self.assertEqual(client.get_url(), url)
        self.assertEqual(client.get_version(), version)
        new_version = self.readonly_version_second
        self.assertTrue(client.update(new_version))
        self.assertEqual(client.get_version(), new_version)
class HGDiffStatClientTest(HGClientTestSetups):
    def setUp(self):
        HGClientTestSetups.setUp(self)
        # after setting up "readonly" repo, change files and make some changes
        subprocess.check_call(["rm", "deleted-fs.txt"], cwd=self.readonly_path)
        subprocess.check_call(["hg", "rm", "deleted.txt"], cwd=self.readonly_path)
        f = io.open(os.path.join(self.readonly_path, "modified.txt"), 'a')
        f.write(u'0123456789abcdef')
        f.close()
        f = io.open(os.path.join(self.readonly_path, "modified-fs.txt"), 'a')
        f.write(u'0123456789abcdef')
        f.close()
        f = io.open(os.path.join(self.readonly_path, "added-fs.txt"), 'w')
        f.write(u'0123456789abcdef')
        f.close()
        f = io.open(os.path.join(self.readonly_path, "added.txt"), 'w')
        f.write(u'0123456789abcdef')
        f.close()
        subprocess.check_call(["hg", "add", "added.txt"], cwd=self.readonly_path)

    def test_diff(self):
        from vcstools.hg import HgClient
        client = HgClient(self.readonly_path)
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEquals('diff --git a/added.txt b/added.txt\nnew file mode 100644\n--- /dev/null\n+++ ./added.txt\n@@ -0,0 +1,1 @@\n+0123456789abcdef\n\\ No newline at end of file\ndiff --git a/deleted.txt b/deleted.txt\ndeleted file mode 100644\ndiff --git a/modified-fs.txt b/modified-fs.txt\n--- ./modified-fs.txt\n+++ ./modified-fs.txt\n@@ -0,0 +1,1 @@\n+0123456789abcdef\n\\ No newline at end of file\ndiff --git a/modified.txt b/modified.txt\n--- ./modified.txt\n+++ ./modified.txt\n@@ -0,0 +1,1 @@\n+0123456789abcdef\n\\ No newline at end of file\n\n', client.get_diff())

    def test_diff_relpath(self):
        from vcstools.hg import HgClient
        client = HgClient(self.readonly_path)
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())

        self.assertEquals('diff --git a/added.txt b/added.txt\nnew file mode 100644\n--- /dev/null\n+++ readonly/added.txt\n@@ -0,0 +1,1 @@\n+0123456789abcdef\n\\ No newline at end of file\ndiff --git a/deleted.txt b/deleted.txt\ndeleted file mode 100644\ndiff --git a/modified-fs.txt b/modified-fs.txt\n--- readonly/modified-fs.txt\n+++ readonly/modified-fs.txt\n@@ -0,0 +1,1 @@\n+0123456789abcdef\n\\ No newline at end of file\ndiff --git a/modified.txt b/modified.txt\n--- readonly/modified.txt\n+++ readonly/modified.txt\n@@ -0,0 +1,1 @@\n+0123456789abcdef\n\\ No newline at end of file\n\n', client.get_diff(basepath=os.path.dirname(self.readonly_path)))

    def test_status(self):
        from vcstools.hg import HgClient
        client = HgClient(self.readonly_path)
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEquals('M modified-fs.txt\nM modified.txt\nA added.txt\nR deleted.txt\n! deleted-fs.txt\n', client.get_status())

    def test_status_relpath(self):
        from vcstools.hg import HgClient
        client = HgClient(self.readonly_path)
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEquals('M readonly/modified-fs.txt\nM readonly/modified.txt\nA readonly/added.txt\nR readonly/deleted.txt\n! readonly/deleted-fs.txt\n', client.get_status(basepath=os.path.dirname(self.readonly_path)))

    def testStatusUntracked(self):
        from vcstools.hg import HgClient
        client = HgClient(self.readonly_path)
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEquals('M modified-fs.txt\nM modified.txt\nA added.txt\nR deleted.txt\n! deleted-fs.txt\n? added-fs.txt\n', client.get_status(untracked=True))

