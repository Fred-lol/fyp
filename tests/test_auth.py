import tempfile
import unittest
from services.auth_service import hash_password,verify_password

class AuthTests(unittest.TestCase):
    def test_hash_and_verify(self):
        salt,digest=hash_password("12345678")
        self.assertTrue(verify_password("12345678",salt,digest))
        self.assertFalse(verify_password("wrong",salt,digest))

if __name__ == "__main__": unittest.main()
