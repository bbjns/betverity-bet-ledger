# BetVerity Bet Ledger

Review actual bet settlements from a local CSV. The ledger totals stakes, paid returns, refunds, and separately charged fees. It reports the net result of closed bets and lists pending stakes separately.

Maintained by BetVerity. [Official BetVerity website](https://betverity.com/) · [BetVerity research and tools](https://betverity.com/tools)

## Run the example

Python 3.9 or later. The tool uses the standard library and reads files locally, with no operator login, API key, or network access.

```sh
python3 bet_ledger.py --csv examples/settlements.csv
```

```text
Currency: USD
  Settled bets:   2
  Fully void:     1
  Closed stakes:  50.00 USD
  Paid returns:   35.00 USD
  Stake refunds:  10.00 USD
  Closed fees:    1.00 USD
  Closed net P/L: -6.00 USD
  Pending bets:   1
  Pending stakes: 5.00 USD
  Pending fees:   0 USD
```

The figures are illustrative. The 10.00 USD stake on the void bet was refunded. The 5.00 USD pending stake has no closed result yet.

## Prepare a statement

Use one account and one currency per CSV. The tool accepts the template in `examples/`. Map your operator statement to it and keep raw statements outside the repository.

| CSV column | What to enter |
| --- | --- |
| `bet_id` | One unique ID per bet. Use one row for the complete current record. |
| `currency` | Three-letter uppercase code, for example USD or EUR. |
| `status` | Use `settled`, `void`, or `pending`. |
| `stake` | Actual positive cash stake debited for this bet. |
| `payout` | Cash payout credited, including returned stake if it is already part of the payout. |
| `refund` | Cash returned as a separate stake refund. |
| `fee` | Separate fee debits. Enter zero if the fee was already deducted from the reported payout. |

Use non-negative numbers with a decimal point and enter zero for amounts that do not apply. A fully void bet should have a full refund and zero payout. For a settled bet with a partial stake refund, use `settled` and record the refund separately. If a bet has a partial payout or refund and remains open, reconcile it when it reaches a final status. A pending bet may include its separately charged fee, which appears under pending fees.

Closed net P/L is paid returns plus refunds, minus closed stakes and closed fees. Count every credit or debit once. Deposits, withdrawals, promotional credits, and non-cash stakes are outside the calculation. The tool reviews historical records only.

## Verify the example

```sh
python3 -m unittest discover -s tests
```

Released under the [MIT License](LICENSE).
