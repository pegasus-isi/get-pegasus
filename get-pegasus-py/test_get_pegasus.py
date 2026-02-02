
import unittest
import unittest.mock
import sys
import os
import platform
import subprocess
import shutil
from pathlib import Path
import tempfile

# Add the script's directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def shell_command(command):
    
    if sys.version_info >= (3, 7):
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    
    # For Python versions < 3.7
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return result.stdout, result.stderr, result.returncode


class TestMainExecution(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory path, but don't create the directory
        self.test_path = Path(tempfile.mkdtemp())
        shutil.rmtree(self.test_path)

    def tearDown(self):
        # The test might create the directory, so we need to clean it up
        if self.test_path.exists():
            shutil.rmtree(self.test_path)
        pass

    def test_main_execution(
        self,
    ):
    
        # Run the script as subprocess
        cmd =  str(Path(__file__).parent / 'get_pegasus.py') + \
               ' --target ' + str(self.test_path)
        out, err, rc = shell_command(cmd)
        print("STDOUT:", out)
        print("STDERR:", err)

        # Verify the script ran successfully
        self.assertEqual(rc, 0)
        
        # Check that the target directory was created
        self.assertTrue(self.test_path.exists())
        
        cmd = f". {self.test_path}/env.sh && condor_master && sleep 10s && condor_status && condor_off", 
        out, err, rc = shell_command(cmd)
        print("STDOUT:", out)
        print("STDERR:", err)
        
        # Verify the sh commands ran successfully
        self.assertEqual(rc, 0)




if __name__ == '__main__':
    unittest.main()
