"""Review actual bet settlements from a local BetVerity-format CSV."""

import argparse
import csv
from dataclasses import dataclass
from decimal import Decimal, localcontext
from pathlib import Path
import re


COLUMNS = ("bet_id", "currency", "status", "stake", "payout", "refund", "fee")
DECIMAL = re.compile(r"[0-9]{1,18}(?:\.[0-9]{1,18})?")
CURRENCY = re.compile(r"[A-Z]{3}")
ZERO = Decimal(0)


@dataclass
class Totals:
    settled_count: int = 0
    void_count: int = 0
    pending_count: int = 0
    closed_stake: Decimal = ZERO
    payout: Decimal = ZERO
    refund: Decimal = ZERO
    fee: Decimal = ZERO
    pending_stake: Decimal = ZERO
    pending_fee: Decimal = ZERO


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        header = reader.fieldnames or []
        if len(header) != len(COLUMNS) or set(header) != set(COLUMNS):
            raise ValueError(f"expected CSV columns {', '.join(COLUMNS)}")
        identifiers = set()
        for row in reader:
            where = f"line {reader.line_num}"
            if None in row or any(value is None or not value.strip() for value in row.values()):
                raise ValueError(f"{where}: expected a value for every CSV column")
            row = {key: value.strip() for key, value in row.items()}
            identifier = row["bet_id"]
            if identifier in identifiers:
                raise ValueError(f"{where}: duplicate bet_id")
            identifiers.add(identifier)
            yield where, row


def amount(value, label, where):
    if not DECIMAL.fullmatch(value):
        raise ValueError(f"{where}: {label} must be a non-negative decimal")
    return Decimal(value)


def reconcile(path):
    currency = None
    total = Totals()
    for where, row in read_rows(path):
        if currency is None:
            currency = row["currency"]
        if not CURRENCY.fullmatch(currency) or row["currency"] != currency:
            raise ValueError(f"{where}: use one three-letter uppercase currency code per file")
        stake, payout, refund, fee = (
            amount(row[name], name, where) for name in ("stake", "payout", "refund", "fee")
        )
        if stake == ZERO or refund > stake:
            raise ValueError(f"{where}: stake must be positive and refund cannot exceed stake")

        status = row["status"]
        if status == "pending":
            if payout or refund:
                raise ValueError(f"{where}: a pending bet cannot include a payout or refund")
            total.pending_count += 1
            total.pending_stake += stake
            total.pending_fee += fee
            continue
        if status == "void":
            if payout or refund != stake:
                raise ValueError(f"{where}: a fully void bet must have zero payout and a full stake refund")
            total.void_count += 1
        elif status == "settled":
            total.settled_count += 1
        else:
            raise ValueError(f"{where}: status must be settled, void, or pending")

        total.closed_stake += stake
        total.payout += payout
        total.refund += refund
        total.fee += fee

    if currency is None:
        raise ValueError("no betting records to reconcile")
    return currency, total


def print_report(currency, total):
    net = total.payout + total.refund - total.closed_stake - total.fee
    print(f"Currency: {currency}")
    print(f"  Settled bets:   {total.settled_count}")
    print(f"  Fully void:     {total.void_count}")
    print(f"  Closed stakes:  {total.closed_stake:f} {currency}")
    print(f"  Paid returns:   {total.payout:f} {currency}")
    print(f"  Stake refunds:  {total.refund:f} {currency}")
    print(f"  Closed fees:    {total.fee:f} {currency}")
    print(f"  Closed net P/L: {net:f} {currency}")
    print(f"  Pending bets:   {total.pending_count}")
    print(f"  Pending stakes: {total.pending_stake:f} {currency}")
    print(f"  Pending fees:   {total.pending_fee:f} {currency}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True, help="BetVerity settlement CSV")
    args = parser.parse_args()
    try:
        with localcontext() as context:
            context.prec = 60
            print_report(*reconcile(args.csv))
    except (OSError, csv.Error, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
