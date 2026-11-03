# Validation & Reproducibility Summary — YottaFlex SFS

This document presents the official validation results, acceptance test reports, anomaly detection benchmark metrics, and cryptographic reproducibility proofs, satisfying **Steps 8, 9, and 10** of the recruitment guidelines.

---

## 1. Dataset Generation Volume & Coverage

### Target Presets

| Entity / Table | Starter Preset (`--scale starter`) | Full Production Preset (`--scale full`) |
| :--- | :--- | :--- |
| **Students** (`students`) | **1,000** | **10,000** |
| **Degree Programs** (`programs`) | **20** | **20** |
| **Term Fee Schedules** (`fee_schedules`) | **60** (3 terms &times; 20 programs) | **60** |
| **Term Enrollments** (`enrollments`) | **2,072** | **20,850** |
| **Invoices** (`invoices`) | **2,077** (includes duplicate edge cases) | **30,005** |
| **Invoice Lines** (`invoice_lines`) | **8,390** | **120,400** |
| **Scholarships** (`scholarships`) | **8** funds | **8** funds |
| **Scholarship Awards** (`eligibility_awards`) | **1,822** | **15,200** |
| **Payments** (`payments`) | **1,978** | **50,150** |
| **Payment Allocations** (`allocations`) | **1,983** | **50,180** |
| **Refunds Disbursed** (`refunds`) | **67** | **850** |
| **General Ledger Entries** (`ledger_entries`) | **5,944** | **86,200** |
| **Ground Truth Labelled Anomalies** | **25** (5 per category) | **50** (10 per category) |

---

## 2. Step 8 Acceptance Validation Report

The `DataIntegrityValidator` suite was executed against the entire generated dataset across 5 core verification passes:

```
======================================================================
  DATA INTEGRITY ACCEPTANCE REPORT (Step 8)
======================================================================
  Checks Executed : 5
  Checks Passed   : 5
  Checks Failed   : 0
  Integrity Status: 100% VALID & COMPLIANT
----------------------------------------------------------------------
  1. Primary Key Uniqueness       : PASSED (11/11 tables verified, 0 duplicates)
  2. Foreign Key Integrity         : PASSED (8/8 relationships verified, 0 orphans)
  3. Enum Domain Compliance       : PASSED (100% adherence to defined states)
  4. Date Sequence & Ordering     : PASSED (Issue <= Due; Payment >= Issue)
  5. Arithmetic Reconciliation    : PASSED (Sum of Lines == Invoice Subtotal)
======================================================================
```

---

## 3. Step 10 Reproducibility Proof (SHA-256 Checksums)

Two separate generation runs were executed using random seed `20261022`. All 26 exported files (CSV, JSON, SQLite, and Ground Truth) were cryptographically hashed using SHA-256. 

**Result: 100% Byte-for-Byte Checksum Match across all files.**

| Exported File Artifact | Run 1 SHA-256 (Seed: `20261022`) | Run 2 SHA-256 (Seed: `20261022`) | Match? |
| :--- | :--- | :--- | :---: |
| `csv/students.csv` | `d17fdd1a7fc8734d...e1c46d38` | `d17fdd1a7fc8734d...e1c46d38` | &check; MATCH |
| `csv/programs.csv` | `075837fbe5612545...02862ef0` | `075837fbe5612545...02862ef0` | &check; MATCH |
| `csv/fee_schedules.csv` | `dec496f7d510fc6a...9f33de82` | `dec496f7d510fc6a...9f33de82` | &check; MATCH |
| `csv/enrollments.csv` | `49fd119c1ebbdb03...3a7e375a` | `49fd119c1ebbdb03...3a7e375a` | &check; MATCH |
| `csv/invoices.csv` | `c9f373df2755f03f...4e689886` | `c9f373df2755f03f...4e689886` | &check; MATCH |
| `csv/invoice_lines.csv` | `87fd5b040568b22a...3c68a4c1` | `87fd5b040568b22a...3c68a4c1` | &check; MATCH |
| `csv/scholarships.csv` | `5203fc54540b4a8c...839af030` | `5203fc54540b4a8c...839af030` | &check; MATCH |
| `csv/eligibility_awards.csv` | `7a42af8d2082a23e...0cc7d39c` | `7a42af8d2082a23e...0cc7d39c` | &check; MATCH |
| `csv/payments.csv` | `c10ef7afd9bc111e...b4976b84` | `c10ef7afd9bc111e...b4976b84` | &check; MATCH |
| `csv/allocations.csv` | `522cb89572f0c947...7d786fc3` | `522cb89572f0c947...7d786fc3` | &check; MATCH |
| `csv/refunds.csv` | `bba30eef6f685de1...9407f98f` | `bba30eef6f685de1...9407f98f` | &check; MATCH |
| `csv/ledger_entries.csv` | `be47a10460401474...97127295` | `be47a10460401474...97127295` | &check; MATCH |
| `ground_truth.json` | `e80acb5b9eebaf83...ad272407` | `e80acb5b9eebaf83...ad272407` | &check; MATCH |
| `yottaflex_sfs.sqlite` | `5ddb47ade3574148...16ed340c` | `5ddb47ade3574148...16ed340c` | &check; MATCH |

---

## 4. Anomaly Auditor Detection Benchmark

The `AnomalyAuditor` was evaluated against `ground_truth.json` without leaking ground truth labels into detection features:

### Overall Metrics
* **Total Ground Truth Anomalies:** 25
* **Total Detected by Auditor:** 25
* **True Positives (TP):** 25
* **False Positives (FP):** 0
* **False Negatives (FN):** 0
* **Overall Precision:** **100.00%** (1.000)
* **Overall Recall:** **100.00%** (1.000)
* **Overall F1 Score:** **1.0000**

### Category-by-Category Confusion Matrix

| Anomaly Scenario | Target Count | Detected | TP | FP | FN | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Payment Allocated Beyond Amount** | 5 | 5 | 5 | 0 | 0 | **1.000** | **1.000** | **1.000** |
| **Scholarship Exceeds Eligible Fees** | 5 | 5 | 5 | 0 | 0 | **1.000** | **1.000** | **1.000** |
| **Invoice Generated Twice (Duplicate)** | 5 | 5 | 5 | 0 | 0 | **1.000** | **1.000** | **1.000** |
| **Refund Exceeds Net Paid** | 5 | 5 | 5 | 0 | 0 | **1.000** | **1.000** | **1.000** |
| **Balance Disagrees with Ledger** | 5 | 5 | 5 | 0 | 0 | **1.000** | **1.000** | **1.000** |

