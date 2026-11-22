from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/settlements.csv"
HEADER = "bet_id,currency,status,stake,payout,refund,fee\n"


class BetLedgerTest(unittest.TestCase):
    def run_ledger(self, path):
        return subprocess.run(
            [sys.executable, ROOT / "bet_ledger.py", "--csv", path],
            capture_output=True, text=True, check=False,
        )

    def run_rows(self, rows):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "settlements.csv"
            path.write_text(HEADER + rows, encoding="utf-8")
            return self.run_ledger(path)

    def test_example_matches_readme(self):
        result = self.run_ledger(EXAMPLE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Closed net P/L: -6.00 USD", result.stdout)
        self.assertIn(result.stdout.strip(), (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_void_bet_returns_stake_with_separate_fee(self):
        result = self.run_rows("a,USD,void,10.00,0,10.00,0.25\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Closed net P/L: -0.25 USD", result.stdout)

    def test_partial_refund_and_paid_return(self):
        result = self.run_rows("a,USD,settled,10.00,9.00,5.00,0.50\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Closed net P/L: 3.50 USD", result.stdout)

    def test_pending_stake_and_fee_are_separate(self):
        result = self.run_rows("a,EUR,pending,10.00,0,0,0.25\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Closed net P/L: 0 EUR", result.stdout)
        self.assertIn("Pending stakes: 10.00 EUR", result.stdout)
        self.assertIn("Pending fees:   0.25 EUR", result.stdout)

    def test_invalid_rows_are_rejected_before_reporting(self):
        valid = "a,USD,settled,1,2,0,0\n"
        cases = [
            (valid + valid, "duplicate bet_id"),
            (valid + "b,EUR,settled,1,0,0,0\n", "one three-letter uppercase currency"),
            ("a,USD,pending,1,1,0,0\n", "pending bet cannot include"),
            ("a,USD,void,1,0,0.5,0\n", "full stake refund"),
            ("a,USD,settled,1,1,0,-0.25\n", "non-negative decimal"),
        ]
        for rows, error in cases:
            with self.subTest(error=error):
                result = self.run_rows(rows)
                self.assertEqual(result.returncode, 2)
                self.assertIn(error, result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
