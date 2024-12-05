import unittest
import tempfile
import os
import shutil
import subprocess
from visualizer import parse_git_object, parse_commit

class TestVisualizer(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the test repository
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        self._remove_temp_dir()

    def _remove_temp_dir(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except PermissionError:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass
        try:
            os.rmdir(self.test_dir)
        except OSError:
            pass

    def test_parse_git_object(self):
        # Initialize a new git repository
        subprocess.run(['git', 'init'], cwd=self.test_dir, check=True)
        with open(os.path.join(self.test_dir, 'file1.txt'), 'w') as f:
            f.write('Hello World')
        # First commit
        subprocess.run(['git', 'add', '.'], cwd=self.test_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=self.test_dir, check=True)
        # Second commit
        with open(os.path.join(self.test_dir, 'file2.txt'), 'w') as f:
            f.write('Another file')
        subprocess.run(['git', 'add', '.'], cwd=self.test_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Second commit'], cwd=self.test_dir, check=True)
        # Get the commit hashes
        commit_hashes = subprocess.check_output(['git', 'rev-list', '--all'], cwd=self.test_dir).decode().splitlines()
        # Test parsing of git objects
        for commit_hash in commit_hashes:
            object_type, data = parse_git_object(self.test_dir, commit_hash)
            self.assertEqual(object_type, 'commit')

    def test_parse_commit(self):
        # Initialize a new git repository
        subprocess.run(['git', 'init'], cwd=self.test_dir, check=True)
        with open(os.path.join(self.test_dir, 'file1.txt'), 'w') as f:
            f.write('Hello World')
        # First commit
        subprocess.run(['git', 'add', '.'], cwd=self.test_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=self.test_dir, check=True)
        # Second commit
        with open(os.path.join(self.test_dir, 'file2.txt'), 'w') as f:
            f.write('Another file')
        subprocess.run(['git', 'add', '.'], cwd=self.test_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Second commit'], cwd=self.test_dir, check=True)
        # Get the commit hashes
        commit_hashes = subprocess.check_output(['git', 'rev-list', '--all'], cwd=self.test_dir).decode().splitlines()
        # Test parsing of commits
        for commit_hash in commit_hashes:
            commit = parse_commit(self.test_dir, commit_hash)
            self.assertEqual(commit.commit_hash, commit_hash)
            # Author date should be an integer timestamp
            self.assertIsInstance(commit.author_date, int)
            # Parents should be a list
            self.assertIsInstance(commit.parents, list)