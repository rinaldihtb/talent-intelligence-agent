import unittest

import pandas as pd


class TestEmbeddingSeeder(unittest.TestCase):
    def test_read_csv(self):
        df = pd.read_csv("data/Resume.csv")
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertIn("ID", df.columns)
        self.assertIn("Resume_str", df.columns)
        self.assertIn("Category", df.columns)


if __name__ == '__main__':
    unittest.main()