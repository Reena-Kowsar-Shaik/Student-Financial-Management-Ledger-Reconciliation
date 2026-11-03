"""
Command-Line Interface for YottaFlex Synthetic Data Generator.
Usage:
    python -m yottaflex.generator.cli --scale starter --seed 20261022
    python -m yottaflex.generator.cli --scale full --seed 20261022 --out data/full
"""

import sys
import time
import argparse
from yottaflex.generator.synthetic import SyntheticDataGenerator


def main():
    parser = argparse.ArgumentParser(
        description="YottaFlex SFS Synthetic Data Generator (Steps 1-10)"
    )
    parser.add_argument(
        "--scale",
        choices=["starter", "full", "custom"],
        default="starter",
        help="Volume preset: 'starter' (~1,000 students), 'full' (10,000 students, 30k invoices), or 'custom'",
    )
    parser.add_argument(
        "--students",
        type=int,
        default=1000,
        help="Number of students to generate if --scale custom (default: 1000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20261022,
        help="Deterministic random seed (default: 20261022)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="data",
        help="Output directory path (default: data)",
    )
    parser.add_argument(
        "--formats",
        type=str,
        default="csv,json,sqlite",
        help="Comma-separated export formats (csv,json,sqlite)",
    )
    parser.add_argument(
        "--no-anomalies",
        action="store_true",
        help="Disable injection of the 5 labelled edge cases",
    )
    parser.add_argument(
        "--anomaly-count",
        type=int,
        default=5,
        help="Number of instances per anomaly category (default: 5)",
    )

    args = parser.parse_args()

    # Determine student count
    if args.scale == "full":
        student_count = 10000
    elif args.scale == "starter":
        student_count = 1000
    else:
        student_count = args.students

    formats = tuple(f.strip() for f in args.formats.split(","))

    print("=" * 70)
    print("  YottaFlex Student Financial System (SFS) Data Generator")
    print("=" * 70)
    print(f" Scale Target   : {args.scale.upper()} ({student_count:,} students)")
    print(f" Random Seed    : {args.seed}")
    print(f" Output Path    : {args.out}")
    print(f" Formats        : {', '.join(formats)}")
    print(f" Inject Anomalies: {not args.no_anomalies} (count={args.anomaly_count}/type)")
    print("-" * 70)

    start_time = time.time()
    generator = SyntheticDataGenerator(seed=args.seed)

    print("Generating master data, enrollments, fee schedules, invoices, and awards...")
    data = generator.generate_all(
        target_students=student_count,
        inject_anomalies=not args.no_anomalies,
        anomaly_count=args.anomaly_count,
    )

    gen_time = time.time() - start_time
    print(f"Generation completed in {gen_time:.2f} seconds.")

    print("\nGenerated Row Counts:")
    for entity_name in [
        "students", "programs", "fee_schedules", "enrollments",
        "invoices", "invoice_lines", "scholarships", "eligibility_awards",
        "payments", "allocations", "refunds", "ledger_entries"
    ]:
        print(f"  - {entity_name:<20}: {len(data[entity_name]):>8,}")
    print(f"  - {'ground_truth anomalies':<20}: {len(data['ground_truth']):>8,}")

    print(f"\nExporting dataset to '{args.out}'...")
    manifest = generator.export_data(data, output_dir=args.out, formats=formats)

    print("\nExported Files & SHA-256 Checksums:")
    for fname, sha in sorted(manifest.items()):
        print(f"  {fname:<30} : {sha[:16]}...{sha[-8:]}")

    total_time = time.time() - start_time
    print("-" * 70)
    print(f"All operations finished successfully in {total_time:.2f}s.")
    print("=" * 70)


if __name__ == "__main__":
    main()
