# Data Dictionary — YottaFlex Student Financial System (SFS)

This document specifies the schema, constraints, domain semantics, and validation rules for all 11 core entities in the YottaFlex Student Financial System, satisfying **Step 1** of the technical problem statement.

---

## 1. Student (`students`)
Master entity representing a learner enrolled in academic programs.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `student_id` | STRING | Required | Format: `STU-\d{6}` | ID | **Unique (PK)** | Immutable, zero-padded 6-digit counter. |
| `first_name` | STRING | Required | Non-empty alphabetic string | Name | Non-unique | Length 2 to 50 chars. |
| `last_name` | STRING | Required | Non-empty alphabetic string | Name | Non-unique | Length 2 to 50 chars. |
| `full_name` | STRING | Derived | `${first_name} ${last_name}` | Name | Non-unique | Computed presentation field. |
| `email` | STRING | Required | Valid RFC 5322 email | Email | **Unique** | Lowercase institutional email address. |
| `residency_status` | ENUM | Required | `IN_STATE`, `OUT_OF_STATE`, `INTERNATIONAL` | Category | Non-unique | Governs tuition schedule multipliers (1.0x, 1.65x, 2.10x). |
| `program_id` | STRING | Required | Foreign Key to `programs.program_id` | ID | Non-unique | Must reference an active academic program. |
| `gpa` | FLOAT | Required | `0.00` to `4.00` | Points | Non-unique | Cumulative GPA rounded to 2 decimal places. |
| `financial_need_score` | FLOAT | Required | `0.0` to `100.0` | Index | Non-unique | Standardized FAFSA-equivalent need metric. |
| `status` | ENUM | Required | `ACTIVE`, `INACTIVE`, `WITHDRAWN`, `GRADUATED` | State | Non-unique | Lifecycle state of student profile. |
| `created_at` | DATE | Required | ISO 8601 (`YYYY-MM-DD`) | Date | Non-unique | Account creation timestamp. |

---

## 2. Program (`programs`)
Master catalog of academic degrees and base fee baselines.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `program_id` | STRING | Required | Format: `PRG-\d{3}` | ID | **Unique (PK)** | Immutable identifier. |
| `name` | STRING | Required | Non-empty text | Title | **Unique** | Degree title (e.g., "B.S. in Computer Science"). |
| `degree_level` | ENUM | Required | `UNDERGRADUATE`, `GRADUATE`, `DOCTORAL` | Level | Non-unique | Academic classification. |
| `department` | STRING | Required | Non-empty text | Dept | Non-unique | Sponsoring academic division. |
| `credits_required` | INTEGER | Required | `30` to `180` | Credits | Non-unique | Graduation credit requirement. |
| `base_tuition_per_credit` | FLOAT | Required | `> 0.00` | USD ($) | Non-unique | Standard per-credit resident tuition. |
| `mandatory_fee` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | Fixed per-term institutional fee. |
| `lab_fee_per_credit` | FLOAT | Optional | `>= 0.00` | USD ($) | Non-unique | Applied to lab-intensive courses. |
| `is_active` | BOOLEAN | Required | `True`, `False` | Flag | Non-unique | Catalog availability flag. |

---

## 3. FeeSchedule (`fee_schedules`)
Term-specific operational fee matrices for degree programs.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `fee_schedule_id` | STRING | Required | `FS-{term_id}-{program_id}` | ID | **Unique (PK)** | Composite deterministic key. |
| `program_id` | STRING | Required | FK to `programs.program_id` | ID | Non-unique | Referential target program. |
| `term_id` | STRING | Required | `TERM-\d{4}-(FALL\|SPRING\|SUMMER)` | Term | Non-unique | Academic session code. |
| `effective_start_date` | DATE | Required | `YYYY-MM-DD` | Date | Non-unique | Term session start date. |
| `effective_end_date` | DATE | Required | `YYYY-MM-DD` | Date | Non-unique | Term session conclusion date (`>= start_date`). |
| `tuition_per_credit` | FLOAT | Required | `> 0.00` | USD ($) | Non-unique | Base per-credit rate. |
| `mandatory_fee` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | Mandatory student activity fee. |
| `technology_fee` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | Campus IT infrastructure fee. |
| `lab_fee_per_credit` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | Departmental laboratory surcharge. |
| `out_of_state_multiplier` | FLOAT | Required | `1.00` to `3.00` | Ratio | Non-unique | Non-resident tuition rate multiplier (1.65x). |
| `international_multiplier` | FLOAT | Required | `1.00` to `4.00` | Ratio | Non-unique | International tuition rate multiplier (2.10x). |
| `late_fee_amount` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | Penalty assessed for overdue accounts. |
| `late_fee_grace_days` | INTEGER | Required | `0` to `60` | Days | Non-unique | Grace period following invoice due date. |

---

## 4. Enrollment (`enrollments`)
Student term registration capturing credit loads and fee waivers.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `enrollment_id` | STRING | Required | `ENR-\d{4}-\d{6}` | ID | **Unique (PK)** | Immutable enrollment identifier. |
| `student_id` | STRING | Required | FK to `students.student_id` | ID | Non-unique | Enrolled student. |
| `program_id` | STRING | Required | FK to `programs.program_id` | ID | Non-unique | Degree program pursued. |
| `term_id` | STRING | Required | Format: `TERM-YYYY-SEASON` | Term | Non-unique | Registration term. |
| `credits_enrolled` | INTEGER | Required | `1` to `24` | Credits | Non-unique | Total term credit hours. |
| `enrollment_date` | DATE | Required | `YYYY-MM-DD` | Date | Non-unique | Registration timestamp (`<= term_start`). |
| `status` | ENUM | Required | `REGISTERED`, `CONFIRMED`, `WITHDRAWN`, `CANCELLED` | State | Non-unique | Registration status lifecycle. |
| `cancellation_date` | DATE | Optional | `YYYY-MM-DD` or NULL | Date | Non-unique | Populated if student drops/withdraws. |
| `fee_waiver_percent` | FLOAT | Optional | `0.0` to `100.0` | Percent | Non-unique | Institutional tuition waiver discount. |

---

## 5. Invoice (`invoices`)
Tuition and fee bill issued to a student for an enrollment term.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `invoice_id` | STRING | Required | `INV-STU-{id}-{year}-{seq}` | ID | **Unique (PK)** | Deterministic invoice identifier. |
| `student_id` | STRING | Required | FK to `students.student_id` | ID | Non-unique | Billed student. |
| `enrollment_id` | STRING | Required | FK to `enrollments.enrollment_id` | ID | Non-unique | Billed registration. |
| `term_id` | STRING | Required | Format: `TERM-YYYY-SEASON` | Term | Non-unique | Term billed. |
| `issue_date` | DATE | Required | `YYYY-MM-DD` | Date | Non-unique | Billing date. |
| `due_date` | DATE | Required | `YYYY-MM-DD` | Date | Non-unique | Payment deadline (`due_date >= issue_date`). |
| `subtotal_amount` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | Sum of all associated `InvoiceLine.line_total`. |
| `scholarship_credit_amount` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | Total scholarship aid credited. |
| `payment_credit_amount` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | Total cash/ACH payments allocated. |
| `balance_due` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | `max(0.0, subtotal - scholarship - payments)`. |
| `status` | ENUM | Required | `DRAFT`, `ISSUED`, `PARTIALLY_PAID`, `PAID`, `OVERDUE`, `CANCELLED` | State | Non-unique | Invoice settlement lifecycle state. |
| `is_duplicate` | BOOLEAN | Optional | `True`, `False` | Flag | Non-unique | Ground-truth flag for duplicate injection. |
| `issue_type` | STRING | Optional | Anomaly code or NULL | Enum | Non-unique | Ground truth label (not in input features). |

---

## 6. InvoiceLine (`invoice_lines`)
Itemized line-item breakdown of charges on an invoice.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `invoice_line_id` | STRING | Required | `INVL-{invoice_id}-{seq}` | ID | **Unique (PK)** | Deterministic line-item identifier. |
| `invoice_id` | STRING | Required | FK to `invoices.invoice_id` | ID | Non-unique | Parent invoice reference. |
| `line_type` | ENUM | Required | `TUITION`, `MANDATORY_FEE`, `LAB_FEE`, `LATE_FEE`, `FEE_WAIVER` | Type | Non-unique | Accounting charge category. |
| `description` | STRING | Required | Non-empty explanatory string | Text | Non-unique | Human-readable explanation with rate details. |
| `unit_amount` | FLOAT | Required | Can be negative for waivers | USD ($) | Non-unique | Per-unit charge or discount. |
| `quantity` | FLOAT | Required | `> 0.0` | Units | Non-unique | Credits or fixed count. |
| `line_total` | FLOAT | Required | `unit_amount * quantity` | USD ($) | Non-unique | Line extension total. |
| `is_scholarship_eligible` | BOOLEAN | Required | `True`, `False` | Flag | Non-unique | Indicates if institutional aid can apply. |

---

## 7. Scholarship (`scholarships`)
Endowment and institutional financial aid programs.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `scholarship_id` | STRING | Required | `SCH-\d{4}-\d{6}` | ID | **Unique (PK)** | Unique fund identifier. |
| `code` | STRING | Required | Alphanumeric code | Code | **Unique** | Administrative shorthand code. |
| `name` | STRING | Required | Non-empty text | Title | Non-unique | Endowment or grant title. |
| `award_type` | ENUM | Required | `MERIT`, `NEED_BASED`, `ATHLETIC`, `DEPARTMENTAL`, `TUITION_WAIVER` | Category | Non-unique | Policy archetype. |
| `funding_source` | STRING | Required | Non-empty text | Agency | Non-unique | Funding entity or endowment source. |
| `max_award_amount` | FLOAT | Required | `> 0.00` | USD ($) | Non-unique | Maximum allowable disbursement cap. |
| `min_gpa` | FLOAT | Optional | `0.00` to `4.00` | Points | Non-unique | Minimum cumulative GPA threshold. |
| `max_financial_need` | FLOAT | Optional | `0.0` to `100.0` | Index | Non-unique | Maximum need index threshold. |
| `eligible_residency` | STRING | Optional | `ALL`, `IN_STATE`, `OUT_OF_STATE`, `INTERNATIONAL` | Code | Non-unique | Geographic eligibility constraint. |
| `covers_tuition_only` | BOOLEAN | Required | `True`, `False` | Flag | Non-unique | If true, restricted to tuition lines only. |
| `is_active` | BOOLEAN | Required | `True`, `False` | Flag | Non-unique | Fund disbursement availability. |

---

## 8. Eligibility (`eligibility_awards`)
Student scholarship qualification evaluation and grant awards.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `award_id` | STRING | Required | `AWD-\d{4}-\d{6}` | ID | **Unique (PK)** | Unique award disbursement record. |
| `scholarship_id` | STRING | Required | FK to `scholarships.scholarship_id` | ID | Non-unique | Reference to scholarship fund. |
| `student_id` | STRING | Required | FK to `students.student_id` | ID | Non-unique | Beneficiary student. |
| `term_id` | STRING | Required | Format: `TERM-YYYY-SEASON` | Term | Non-unique | Applicable academic term. |
| `award_amount` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | Final grant amount applied. |
| `eligible_amount` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | Net qualifying tuition/fee total. |
| `status` | ENUM | Required | `ELIGIBLE`, `AWARDED`, `APPLIED`, `REVOKED`, `REJECTED` | State | Non-unique | Evaluation and disbursement lifecycle. |
| `decision_rationale` | STRING | Required | Explanatory text | Text | Non-unique | Audit log with GPA, need, and caps. |
| `evaluation_date` | DATE | Required | `YYYY-MM-DD` | Date | Non-unique | Adjudication timestamp. |
| `issue_type` | STRING | Optional | Anomaly code or NULL | Enum | Non-unique | Ground truth label (not in features). |

---

## 9. Payment (`payments`)
Cash receipts and settlement transactions from students or third-party sponsors.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `payment_id` | STRING | Required | `PAY-\d{4}-\d{6}` | ID | **Unique (PK)** | Immutable payment reference. |
| `student_id` | STRING | Required | FK to `students.student_id` | ID | Non-unique | Payer student. |
| `term_id` | STRING | Required | Format: `TERM-YYYY-SEASON` | Term | Non-unique | Session credited. |
| `payment_date` | DATE | Required | `YYYY-MM-DD` | Date | Non-unique | Transaction settlement date. |
| `payment_method` | ENUM | Required | `CREDIT_CARD`, `ACH_TRANSFER`, `WIRE`, `THIRD_PARTY`, `CASH` | Method | Non-unique | Financial tender channel. |
| `total_amount` | FLOAT | Required | `> 0.00` | USD ($) | Non-unique | Settled cash amount received. |
| `allocated_amount` | FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | `sum(PaymentAllocation.allocated_amount)`. |
| `unallocated_amount`| FLOAT | Required | `>= 0.00` | USD ($) | Non-unique | `total_amount - allocated_amount` (Credit). |
| `status` | ENUM | Required | `PENDING`, `SETTLED`, `FAILED`, `REFUNDED`, `PARTIALLY_REFUNDED` | State | Non-unique | Banking settlement status. |
| `transaction_reference` | STRING | Required | Alphanumeric transaction string | Ref | Non-unique | External gateway or bank clearing ID. |
| `issue_type` | STRING | Optional | Anomaly code or NULL | Enum | Non-unique | Ground truth label (not in features). |

---

## 10. PaymentAllocation (`allocations`)
Ledger mapping of cash payments applied against specific invoice balances.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `allocation_id` | STRING | Required | `ALLOC-{payment_id}-{seq}` | ID | **Unique (PK)** | Deterministic allocation record. |
| `payment_id` | STRING | Required | FK to `payments.payment_id` | ID | Non-unique | Source payment record. |
| `invoice_id` | STRING | Required | FK to `invoices.invoice_id` | ID | Non-unique | Target invoice credited. |
| `invoice_line_id` | STRING | Optional | FK to `invoice_lines.invoice_line_id` | ID | Non-unique | Optional itemized line mapping. |
| `allocated_amount` | FLOAT | Required | `> 0.00` | USD ($) | Non-unique | Portion of payment applied. |
| `allocation_date` | DATE | Required | `YYYY-MM-DD` | Date | Non-unique | Date funds applied (`>= payment_date`). |
| `status` | ENUM | Required | `ALLOCATED`, `REVERSED` | State | Non-unique | Allocation ledger status. |

---

## 11. Refund (`refunds`)
Cash disbursements returned to students for drops, withdrawals, or credit balances.

| Field Name | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `refund_id` | STRING | Required | `REF-\d{4}-\d{6}` | ID | **Unique (PK)** | Immutable refund disbursement ID. |
| `student_id` | STRING | Required | FK to `students.student_id` | ID | Non-unique | Recipient student. |
| `payment_id` | STRING | Required | FK to `payments.payment_id` | ID | Non-unique | Source settlement refunded. |
| `term_id` | STRING | Required | Format: `TERM-YYYY-SEASON` | Term | Non-unique | Relevant academic term. |
| `request_date` | DATE | Required | `YYYY-MM-DD` | Date | Non-unique | Refund request submission date. |
| `processed_date` | DATE | Optional | `YYYY-MM-DD` or NULL | Date | Non-unique | Disbursement date (`>= request_date`). |
| `refund_amount` | FLOAT | Required | `> 0.00` | USD ($) | Non-unique | Dollar amount refunded. |
| `reason` | ENUM | Required | `WITHDRAWAL`, `OVERPAYMENT`, `WAIVER_ADJUSTMENT`, `ERROR_CORRECTION` | Code | Non-unique | Business justification. |
| `status` | ENUM | Required | `REQUESTED`, `APPROVED`, `PROCESSED`, `REJECTED` | State | Non-unique | Approval and disbursement lifecycle. |
| `approval_notes` | STRING | Optional | Text | Notes | Non-unique | Bursar / financial aid authorization note. |
| `issue_type` | STRING | Optional | Anomaly code or NULL | Enum | Non-unique | Ground truth label (not in features). |
