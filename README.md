# YottaFlex Student Financial System (SFS)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-20%20passed%20(100%25)-brightgreen.svg)]()
[![Precision/Recall](https://img.shields.io/badge/Auditor%20F1%20Score-1.000-success.svg)]()
[![Seed Reproducibility](https://img.shields.io/badge/Step%2010%20Reproducibility-Verified%20(SHA--256)-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

> **Recruitment Drive:** Round 3 — 72-Hour Code Challenge  
> **Candidate:** Shaik Reena Kowsar  
> **Target Role:** Associate AI Forward Deployed Engineer  
> **Submission Window:** November 2 – November 5, 2026  

---

## Table of Contents
1. [Overview & Business Scope](#overview--business-scope)
2. [Quickstart: Make It Run in 60 Seconds](#quickstart-make-it-run-in-60-seconds)
3. [Synthetic Data Generator CLI (Steps 1–10)](#synthetic-data-generator-cli-steps-110)
4. [Running the Automated Test Suite](#running-the-automated-test-suite)
5. [Interactive Web Dashboard & REST API](#interactive-web-dashboard--rest-api)
6. [Auditor & Anomaly Detection Performance](#auditor--anomaly-detection-performance)
7. [Step 10 Deterministic Reproducibility Proof](#step-10-deterministic-reproducibility-proof)
8. [Project Layout](#project-layout)
9. [Documentation Deliverables](#documentation-deliverables)

---

## Overview & Business Scope

The **YottaFlex Student Financial System (SFS)** is an end-to-end higher education financial platform that calculates tuition and fees, applies scholarship eligibility criteria, allocates payments using FIFO rules, manages refund schedules, and maintains an immutable double-entry general ledger.

### Key Capabilities
* **Dynamic Fee Calculation:** Itemizes tuition, mandatory student services fees, technology fees, lab charges, and approved fee waivers based on student residency (In-State 1.0x, Out-of-State 1.65x, International 2.10x).
* **Scholarship Adjudication:** Enforces GPA thresholds, financial need scoring, residency filters, and ensures institutional awards never exceed net tuition obligations.
* **Payment Allocation Engine:** Multi-invoice FIFO settlement with unallocated overpayment credit retention.
* **Refund Manager:** Validates withdrawals and enforces net-paid bounds (`refund <= settled payments - prior refunds`).
* **General Ledger & Reconciler:** Double-entry immutable accounting event trail (Debits vs Credits) with 0-discrepancy reconciliation.
* **1-Click Anomaly Auditor:** Identifies the 5 required edge cases with **100% Precision, 100% Recall, and 1.000 F1 Score** against decoupled ground truth.

---

## Quickstart: Make It Run in 60 Seconds

### Prerequisites
* Python 3.10+ (Tested on Python 3.11.9)
* Git

### 1. Clone & Set Up Environment
```bash
git clone <your-public-repo-url>
cd YottaFlex

# Optional: Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate the Dataset
```bash
# Starter scale (~1,000 students, 2,077 invoices, CSV/JSON/SQLite exports)
python -m yottaflex.generator.cli --scale starter --seed 20261022 --out data

# Or full production volume (10,000 students, 30,000 invoices, 50,000 payments)
python -m yottaflex.generator.cli --scale full --seed 20261022 --out data/full
```

### 3. Run the Automated Test Suite
```bash
# Runs all 20 unit, acceptance, and reproducibility tests
python -m unittest discover tests
```

### 4. Launch the Interactive Web Dashboard
```bash
python -m yottaflex.web.app
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser to inspect the student 360 portal, run the live anomaly auditor, and use the interactive financial simulator.

---

## Synthetic Data Generator CLI (Steps 1–10)

The generator is parameterized and deterministic.

```bash
python -m yottaflex.generator.cli [OPTIONS]
```

### Supported Arguments
| Flag | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--scale` | choice | `starter` | Volume preset: `starter` (1k students), `full` (10k students), or `custom`. |
| `--students` | int | `1000` | Custom number of students when `--scale custom`. |
| `--seed` | int | `20261022` | Deterministic random seed for reproducibility. |
| `--out` | string | `data` | Directory where CSV, JSON, and SQLite files are exported. |
| `--formats` | string | `csv,json,sqlite` | Comma-separated list of export formats. |
| `--no-anomalies` | flag | `False` | Disables edge-case anomaly injection. |
| `--anomaly-count`| int | `5` | Number of instances to inject per anomaly scenario. |

### Generated Outputs
Running the generator populates the output folder with:
* `data/csv/*.csv`: Relational tables for all 11 core entities + ledger entries.
* `data/json/*.json`: JSON serialization for API ingestion.
* `data/yottaflex_sfs.sqlite`: Zero-configuration SQLite database with foreign keys.
* `data/ground_truth.json`: Decoupled ground truth labels for anomaly benchmarks.

---

## Running the Automated Test Suite

The test suite requires zero external dependencies and runs under Python's native `unittest` framework:

```bash
python -m unittest discover tests -v
```

### Test Coverage Highlights
* `test_fee_calculator.py`: Validates residency multipliers, fee line itemization, fee waiver discounts, and late fee grace periods.
* `test_scholarship_engine.py`: Validates merit/need eligibility rules, eligible tuition caps, and net fee waiver interactions.
* `test_payment_allocator.py`: Validates FIFO multi-invoice allocation, partial settlements, and overpayment credits.
* `test_refund_manager.py`: Tests net-paid boundary enforcement and rejection of unauthorized refunds.
* `test_ledger_reconciler.py`: Verifies double-entry ledger balance equations and discrepancy detection.
* `test_data_integrity.py`: Executes Step 8 acceptance verification (PK uniqueness, FK integrity, enum compliance, date ordering, arithmetic consistency).
* `test_anomaly_auditor.py`: Asserts 1.000 F1 score across all 5 edge cases against ground truth.
* `test_reproducibility.py`: Executes Step 10 by generating twice and checking byte-for-byte SHA-256 equality.

---

## Interactive Web Dashboard & REST API

The interactive web console provides four operational consoles:

1. **Executive Financial Summary:** Real-time KPI cards displaying Total Invoiced, Scholarships Awarded, Payments Settled, Net Receivables, and Collection Rate.
2. **Student 360 Account Portal:** Live directory search by student ID or name, itemized invoice breakdown, scholarship rationale inspector, and immutable general ledger audit trail.
3. **1-Click Anomaly Auditor:** Triggers the audit engine against the active dataset, displaying live precision, recall, and category-level confusion matrices against `ground_truth.json`.
4. **Interactive Financial Simulator:**
   * Calculate real-time tuition for any credit load, degree program, and residency status.
   * Evaluate candidate scholarship eligibility against GPA, financial need, and tuition caps.

---

## Auditor & Anomaly Detection Performance

Evaluated against the 5 required edge cases in `ground_truth.json`:

| Anomaly Scenario | Target Count | Detected | TP | FP | FN | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Payment Allocated Beyond Amount** | 5 | 5 | 5 | 0 | 0 | **100%** | **100%** | **1.000** |
| **Scholarship Exceeds Eligible Fees** | 5 | 5 | 5 | 0 | 0 | **100%** | **100%** | **1.000** |
| **Invoice Generated Twice (Duplicate)** | 5 | 5 | 5 | 0 | 0 | **100%** | **100%** | **1.000** |
| **Refund Exceeds Net Paid** | 5 | 5 | 5 | 0 | 0 | **100%** | **100%** | **1.000** |
| **Balance Disagrees with Ledger** | 5 | 5 | 5 | 0 | 0 | **100%** | **100%** | **1.000** |
| **OVERALL SYSTEM TOTAL** | **25** | **25** | **25** | **0** | **0** | **100.0%**| **100.0%**| **1.0000**|

---

## Step 10 Deterministic Reproducibility Proof

To verify Step 10 reproducibility, run:

```bash
python -c "
from yottaflex.generator.synthetic import SyntheticDataGenerator
import shutil

gen1 = SyntheticDataGenerator(seed=20261022)
m1 = gen1.export_data(gen1.generate_all(target_students=300), output_dir='data/run1')

gen2 = SyntheticDataGenerator(seed=20261022)
m2 = gen2.export_data(gen2.generate_all(target_students=300), output_dir='data/run2')

for f in m1:
    assert m1[f] == m2[f], f'Mismatch in {f}'
print('All 26 files matched with identical SHA-256 checksums!')
shutil.rmtree('data/run1')
shutil.rmtree('data/run2')
"
```

---

## Project Layout

```
d:\YottaFlex/
├── README.md                      # Comprehensive execution and verification guide
├── DATA_DICTIONARY.md             # Granular specifications for all 11 entities (Step 1)
├── ARCHITECTURE.md                # System architecture, Mermaid diagrams & trade-offs (Guideline 04)
├── AI_COLLABORATION.md            # Full prompt history & LLM transparency log (Guideline 03)
├── VALIDATION_SUMMARY.md          # Acceptance reports, row counts & checksum proofs (Steps 8-10)
├── requirements.txt               # Project dependencies
├── yottaflex/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py               # Domain enumerations (Residency, Statuses, AnomalyTypes)
│   │   └── entities.py            # Dataclasses & serializable models for all 11 entities
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── fee_calculator.py      # Tuition, fee schedules, multipliers & late fees
│   │   ├── scholarship_engine.py  # Eligibility rules, caps & net-tuition waiver logic
│   │   ├── payment_allocator.py   # FIFO invoice allocation & overpayment credit ledger
│   │   ├── refund_manager.py      # Withdrawal schedules & net-paid boundary checks
│   │   ├── ledger_reconciler.py   # Double-entry general ledger & balance reconciliation
│   │   └── anomaly_auditor.py     # Root-cause rule exception detector & metrics evaluator
│   ├── generator/
│   │   ├── __init__.py
│   │   ├── cli.py                 # Parameterized CLI entrypoint (--scale, --seed)
│   │   ├── synthetic.py           # 10-step deterministic synthetic data pipeline
│   │   └── edge_cases.py          # Labelled anomaly injectors & ground-truth builder
│   ├── validator/
│   │   ├── __init__.py
│   │   └── data_integrity.py      # Step 8 validation: PK, FK, enums, dates, arithmetic
│   └── web/
│       ├── __init__.py
│       └── app.py                 # Flask web dashboard and REST API
├── tests/
│   ├── __init__.py
│   ├── test_fee_calculator.py     # Tuition calculation tests
│   ├── test_scholarship_engine.py # Scholarship eligibility tests
│   ├── test_payment_allocator.py  # FIFO payment allocation tests
│   ├── test_refund_manager.py     # Net-paid refund constraint tests
│   ├── test_ledger_reconciler.py  # Account balance reconciliation tests
│   ├── test_data_integrity.py     # Step 8 data integrity acceptance tests
│   ├── test_anomaly_auditor.py    # Anomaly detection 1.000 F1 score benchmark
│   └── test_reproducibility.py    # Step 10 SHA-256 reproducibility tests
└── data/                          # Exported CSV, JSON, SQLite & ground_truth.json
```

---

## Documentation Deliverables

* **[DATA_DICTIONARY.md](file:///d:/YottaFlex/DATA_DICTIONARY.md):** Granular field-by-field schema for all 11 entities.
* **[ARCHITECTURE.md](file:///d:/YottaFlex/ARCHITECTURE.md):** Architectural design, sequence diagrams, state machines, and technical trade-offs.
* **[AI_COLLABORATION.md](file:///d:/YottaFlex/AI_COLLABORATION.md):** Comprehensive prompt history, AI assistance log, and candidate review points.
* **[VALIDATION_SUMMARY.md](file:///d:/YottaFlex/VALIDATION_SUMMARY.md):** Acceptance test outputs, row counts, and checksum manifests.

