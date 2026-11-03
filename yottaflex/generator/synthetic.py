"""
Deterministic Synthetic Data Generator for YottaFlex SFS.
Implements Steps 1 through 10 of the recruitment drive guidelines.
"""

import os
import csv
import json
import random
import hashlib
import sqlite3
from typing import Dict, List, Any, Tuple
from datetime import datetime, date, timedelta

from yottaflex.models.enums import (
    ResidencyStatus,
    StudentStatus,
    DegreeLevel,
    EnrollmentStatus,
    InvoiceStatus,
    InvoiceLineType,
    ScholarshipType,
    ScholarshipStatus,
    PaymentMethod,
    PaymentStatus,
    RefundReason,
    RefundStatus,
)
from yottaflex.models.entities import (
    Student,
    Program,
    FeeSchedule,
    Enrollment,
    Invoice,
    InvoiceLine,
    Scholarship,
    Eligibility,
    Payment,
    PaymentAllocation,
    Refund,
    StudentLedgerEntry,
)
from yottaflex.engine.fee_calculator import FeeCalculator
from yottaflex.engine.scholarship_engine import ScholarshipEngine
from yottaflex.engine.payment_allocator import PaymentAllocator
from yottaflex.engine.refund_manager import RefundManager
from yottaflex.engine.ledger_reconciler import LedgerReconciler
from yottaflex.generator.edge_cases import EdgeCaseInjector


class SyntheticDataGenerator:
    """
    High-performance, deterministic synthetic data generator.
    """

    FIRST_NAMES = [
        "Aarav", "Aditi", "Alexander", "Amara", "Arjun", "Chloe", "David", "Elena",
        "Fatima", "Gabriel", "Hassan", "Ishaan", "Jasmine", "Kavya", "Liam", "Maya",
        "Noah", "Olivia", "Priya", "Rahul", "Riya", "Samuel", "Sophia", "Tariq",
        "Vikram", "Zara", "Daniel", "Emma", "Lucas", "Mei", "Dev", "Ananya"
    ]

    LAST_NAMES = [
        "Sharma", "Patel", "Johnson", "Smith", "Williams", "Chen", "Gupta", "Garcia",
        "Khan", "Rodriguez", "Kim", "Nguyen", "Reddy", "Mehta", "Brown", "Davis",
        "Wilson", "Iyer", "Choudhury", "Nair", "Taylor", "Anderson", "Thomas", "Ali"
    ]

    PROGRAM_SPECS = [
        ("PRG-001", "B.S. in Computer Science", DegreeLevel.UNDERGRADUATE, "School of Computing", 120, 520.00, 350.00, 45.00),
        ("PRG-002", "B.S. in Artificial Intelligence", DegreeLevel.UNDERGRADUATE, "School of Computing", 120, 540.00, 350.00, 60.00),
        ("PRG-003", "B.S. in Data Science", DegreeLevel.UNDERGRADUATE, "School of Computing", 120, 530.00, 350.00, 50.00),
        ("PRG-004", "B.S. in Cybersecurity", DegreeLevel.UNDERGRADUATE, "School of Computing", 120, 510.00, 350.00, 40.00),
        ("PRG-005", "B.S. in Electrical Engineering", DegreeLevel.UNDERGRADUATE, "School of Engineering", 128, 550.00, 400.00, 75.00),
        ("PRG-006", "B.S. in Mechanical Engineering", DegreeLevel.UNDERGRADUATE, "School of Engineering", 128, 550.00, 400.00, 75.00),
        ("PRG-007", "B.S. in Biomedical Engineering", DegreeLevel.UNDERGRADUATE, "School of Engineering", 128, 560.00, 420.00, 80.00),
        ("PRG-008", "B.S. in Business Administration", DegreeLevel.UNDERGRADUATE, "School of Business", 120, 480.00, 300.00, 15.00),
        ("PRG-009", "B.S. in Finance & FinTech", DegreeLevel.UNDERGRADUATE, "School of Business", 120, 500.00, 320.00, 25.00),
        ("PRG-010", "B.S. in Biotechnology", DegreeLevel.UNDERGRADUATE, "School of Sciences", 120, 510.00, 380.00, 70.00),
        ("PRG-011", "M.S. in Computer Science", DegreeLevel.GRADUATE, "School of Computing", 36, 780.00, 450.00, 65.00),
        ("PRG-012", "M.S. in Machine Learning & AI", DegreeLevel.GRADUATE, "School of Computing", 36, 820.00, 480.00, 85.00),
        ("PRG-013", "M.S. in Data Engineering", DegreeLevel.GRADUATE, "School of Computing", 36, 790.00, 450.00, 70.00),
        ("PRG-014", "M.S. in Cybersecurity Operations", DegreeLevel.GRADUATE, "School of Computing", 36, 770.00, 450.00, 60.00),
        ("PRG-015", "M.S. in Robotics & Autonomous Systems", DegreeLevel.GRADUATE, "School of Engineering", 36, 830.00, 500.00, 95.00),
        ("PRG-016", "Master of Business Administration (MBA)", DegreeLevel.GRADUATE, "School of Business", 48, 920.00, 550.00, 30.00),
        ("PRG-017", "M.S. in Health Informatics", DegreeLevel.GRADUATE, "School of Health", 36, 750.00, 420.00, 45.00),
        ("PRG-018", "Ph.D. in Computer Science", DegreeLevel.DOCTORAL, "School of Computing", 72, 850.00, 300.00, 50.00),
        ("PRG-019", "Ph.D. in Artificial Intelligence", DegreeLevel.DOCTORAL, "School of Computing", 72, 870.00, 300.00, 50.00),
        ("PRG-020", "Ph.D. in Bioengineering", DegreeLevel.DOCTORAL, "School of Engineering", 72, 880.00, 300.00, 60.00),
    ]

    TERMS = [
        ("TERM-2026-FALL", "2026-08-25", "2026-12-18", "2026-08-15"),
        ("TERM-2027-SPRING", "2027-01-15", "2027-05-15", "2027-01-05"),
        ("TERM-2027-SUMMER", "2027-06-01", "2027-08-10", "2027-05-20"),
    ]

    def __init__(self, seed: int = 20261022):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_all(
        self,
        target_students: int = 1000,
        inject_anomalies: bool = True,
        anomaly_count: int = 5,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end data generation matching the specified volume.
        """
        # Step 2: Create parent/master records first
        programs = self._generate_programs()
        fee_schedules = self._generate_fee_schedules(programs)
        scholarships = self._generate_scholarships()
        students = self._generate_students(target_students, programs)

        # Step 3: Create child enrollments and invoices
        enrollments, invoices, invoice_lines = self._generate_enrollments_and_invoices(
            students, programs, fee_schedules
        )

        # Step 4: Evaluate and apply scholarships
        awards = self._generate_scholarship_awards(students, scholarships, invoices, invoice_lines)

        # Step 5: Generate payments and allocate
        payments, allocations = self._generate_payments_and_allocations(students, invoices, invoice_lines)

        # Step 6: Process withdrawals and refunds
        refunds = self._generate_refunds(students, payments, enrollments)

        # Step 7: Inject labelled edge cases if requested
        ground_truth: List[Dict[str, Any]] = []
        if inject_anomalies:
            ground_truth, _ = EdgeCaseInjector.inject_all_edge_cases(
                invoices=invoices,
                invoice_lines=invoice_lines,
                awards=awards,
                payments=payments,
                allocations=allocations,
                refunds=refunds,
                students=students,
                count_per_type=anomaly_count,
            )

        # Step 8: Build ledger entries for auditability
        all_ledger_entries = []
        for s in students:
            stu_entries = LedgerReconciler.generate_ledger_entries(
                student_id=s.student_id,
                invoices=invoices,
                awards=awards,
                payments=payments,
                refunds=refunds,
            )
            all_ledger_entries.extend(stu_entries)

        return {
            "students": students,
            "programs": programs,
            "fee_schedules": fee_schedules,
            "enrollments": enrollments,
            "invoices": invoices,
            "invoice_lines": invoice_lines,
            "scholarships": scholarships,
            "eligibility_awards": awards,
            "payments": payments,
            "allocations": allocations,
            "refunds": refunds,
            "ledger_entries": all_ledger_entries,
            "ground_truth": ground_truth,
        }

    def _generate_programs(self) -> List[Program]:
        programs = []
        for pid, name, level, dept, credits, tuition, fee, lab in self.PROGRAM_SPECS:
            programs.append(
                Program(
                    program_id=pid,
                    name=name,
                    degree_level=level,
                    department=dept,
                    credits_required=credits,
                    base_tuition_per_credit=tuition,
                    mandatory_fee=fee,
                    lab_fee_per_credit=lab,
                    is_active=True,
                )
            )
        return programs

    def _generate_fee_schedules(self, programs: List[Program]) -> List[FeeSchedule]:
        schedules = []
        for term_id, start_dt, end_dt, _ in self.TERMS:
            for prog in programs:
                fs_id = f"FS-{term_id}-{prog.program_id}"
                schedules.append(
                    FeeSchedule(
                        fee_schedule_id=fs_id,
                        program_id=prog.program_id,
                        term_id=term_id,
                        effective_start_date=start_dt,
                        effective_end_date=end_dt,
                        tuition_per_credit=prog.base_tuition_per_credit,
                        mandatory_fee=prog.mandatory_fee,
                        technology_fee=125.00,
                        lab_fee_per_credit=prog.lab_fee_per_credit,
                        out_of_state_multiplier=1.65,
                        international_multiplier=2.10,
                        late_fee_amount=75.00,
                        late_fee_grace_days=14,
                    )
                )
        return schedules

    def _generate_scholarships(self) -> List[Scholarship]:
        specs = [
            ("SCH-2026-000001", "PRES-EXCELLENCE", "Presidential Academic Excellence Scholarship", ScholarshipType.MERIT, "Endowment Fund", 8000.00, 3.85, 100.0, "ALL", True),
            ("SCH-2026-000002", "DEAN-STEM", "Dean's STEM Leadership Scholarship", ScholarshipType.MERIT, "College Foundation", 5000.00, 3.50, 100.0, "ALL", True),
            ("SCH-2026-000003", "OPPORTUNITY-GRANT", "First-Generation College Opportunity Grant", ScholarshipType.NEED_BASED, "State Aid Grant", 6000.00, 2.50, 60.0, "IN_STATE", False),
            ("SCH-2026-000004", "TECH-EQUITY", "YottaFlex Future Technologist Award", ScholarshipType.NEED_BASED, "Corporate Partnership", 4500.00, 3.00, 50.0, "ALL", True),
            ("SCH-2026-000005", "ATHLETIC-D1", "Varsity Athletic Distinction Award", ScholarshipType.ATHLETIC, "Athletic Department", 7500.00, 2.75, 100.0, "ALL", False),
            ("SCH-2026-000006", "COMP-GRAD-FELLOW", "Computing Graduate Research Fellowship", ScholarshipType.DEPARTMENTAL, "NSF Grant", 10000.00, 3.70, 100.0, "ALL", True),
            ("SCH-2026-000007", "RESIDENT-SUCCESS", "State Resident Education Incentive", ScholarshipType.TUITION_WAIVER, "State Treasury", 3000.00, 2.80, 100.0, "IN_STATE", True),
            ("SCH-2026-000008", "GLOBAL-SCHOLAR", "Global Diversity Academic Fellowship", ScholarshipType.MERIT, "International Office", 6500.00, 3.60, 100.0, "INTERNATIONAL", True),
        ]
        return [
            Scholarship(
                scholarship_id=sid,
                code=code,
                name=name,
                award_type=atype,
                funding_source=src,
                max_award_amount=amt,
                min_gpa=gpa,
                max_financial_need=need,
                eligible_residency=res,
                covers_tuition_only=cov,
                is_active=True,
            )
            for sid, code, name, atype, src, amt, gpa, need, res, cov in specs
        ]

    def _generate_students(self, count: int, programs: List[Program]) -> List[Student]:
        students = []
        residency_choices = [
            ResidencyStatus.IN_STATE,
            ResidencyStatus.OUT_OF_STATE,
            ResidencyStatus.INTERNATIONAL,
        ]
        residency_weights = [0.60, 0.25, 0.15]
        prog_ids = [p.program_id for p in programs]

        for i in range(1, count + 1):
            sid = f"STU-{i:06d}"
            fn = self.rng.choice(self.FIRST_NAMES)
            ln = self.rng.choice(self.LAST_NAMES)
            email = f"{fn.lower()}.{ln.lower()}{i:02d}@student.university.edu"
            res = self.rng.choices(residency_choices, weights=residency_weights)[0]
            gpa = min(4.0, max(2.0, round(self.rng.gauss(3.3, 0.45), 2)))
            need = min(100.0, max(0.0, round(self.rng.gauss(55.0, 25.0), 1)))
            pid = self.rng.choice(prog_ids)

            students.append(
                Student(
                    student_id=sid,
                    first_name=fn,
                    last_name=ln,
                    email=email,
                    residency_status=res,
                    program_id=pid,
                    gpa=gpa,
                    financial_need_score=need,
                    status=StudentStatus.ACTIVE,
                    created_at="2026-07-01",
                )
            )
        return students

    def _generate_enrollments_and_invoices(
        self,
        students: List[Student],
        programs: List[Program],
        fee_schedules: List[FeeSchedule],
    ) -> Tuple[List[Enrollment], List[Invoice], List[InvoiceLine]]:
        enrollments = []
        invoices = []
        invoice_lines = []

        prog_map = {p.program_id: p for p in programs}
        fs_map = {(fs.term_id, fs.program_id): fs for fs in fee_schedules}

        enr_counter = 1
        inv_counter = 1

        for term_idx, (term_id, _, _, issue_dt) in enumerate(self.TERMS):
            # For starter scale: every student enrolled in Fall; a subset in Spring/Summer
            for stu in students:
                # 90% enrolled in Fall, 85% Spring, 30% Summer
                enroll_prob = 0.95 if term_idx == 0 else (0.85 if term_idx == 1 else 0.30)
                if self.rng.random() > enroll_prob:
                    continue

                prog = prog_map[stu.program_id]
                fs = fs_map.get((term_id, prog.program_id))
                if not fs:
                    continue

                # Credits enrolled
                if prog.degree_level == DegreeLevel.UNDERGRADUATE:
                    credits = self.rng.choice([12, 14, 15, 16, 18])
                else:
                    credits = self.rng.choice([9, 10, 12])

                # Fee waiver probability (~4% students have academic waiver)
                waiver_pct = 25.0 if self.rng.random() < 0.04 else 0.0

                enr_id = f"ENR-2026-{enr_counter:06d}"
                enr_counter += 1

                enrollment = Enrollment(
                    enrollment_id=enr_id,
                    student_id=stu.student_id,
                    program_id=prog.program_id,
                    term_id=term_id,
                    credits_enrolled=credits,
                    enrollment_date=issue_dt,
                    status=EnrollmentStatus.CONFIRMED,
                    fee_waiver_percent=waiver_pct,
                )
                enrollments.append(enrollment)

                # Generate Invoice & Lines via FeeCalculator
                inv_id = f"INV-STU-{stu.student_id[4:]}-2026-{inv_counter:06d}"
                inv_counter += 1

                invoice, lines = FeeCalculator.generate_invoice(
                    invoice_id=inv_id,
                    student=stu,
                    program=prog,
                    fee_schedule=fs,
                    enrollment=enrollment,
                    issue_date=issue_dt,
                )
                invoices.append(invoice)
                invoice_lines.extend(lines)

        return enrollments, invoices, invoice_lines

    def _generate_scholarship_awards(
        self,
        students: List[Student],
        scholarships: List[Scholarship],
        invoices: List[Invoice],
        invoice_lines: List[InvoiceLine],
    ) -> List[Eligibility]:
        awards = []
        lines_by_inv = {}
        for l in invoice_lines:
            lines_by_inv.setdefault(l.invoice_id, []).append(l)

        stu_map = {s.student_id: s for s in students}
        award_counter = 1

        # Evaluate scholarships for open invoices
        for inv in invoices:
            stu = stu_map.get(inv.student_id)
            if not stu:
                continue

            inv_lines = lines_by_inv.get(inv.invoice_id, [])

            # Chance of student receiving a scholarship based on GPA & Need
            for sch in scholarships:
                # Check residency match
                if sch.eligible_residency and sch.eligible_residency != "ALL":
                    if stu.residency_status.value != sch.eligible_residency:
                        continue

                # Check GPA / Need eligibility
                if stu.gpa >= sch.min_gpa and (sch.award_type != ScholarshipType.NEED_BASED or stu.financial_need_score >= 40.0):
                    # Eligible candidate! Award with 75% probability if qualified
                    if self.rng.random() < 0.75:
                        awd_id = f"AWD-2026-{award_counter:06d}"
                        award_counter += 1
                        award = ScholarshipEngine.evaluate_eligibility(
                            award_id=awd_id,
                            student=stu,
                            scholarship=sch,
                            term_id=inv.term_id,
                            invoice_lines=inv_lines,
                            evaluation_date=inv.issue_date,
                        )
                        if award.status == ScholarshipStatus.AWARDED:
                            ScholarshipEngine.apply_award_to_invoice(award, inv)
                            awards.append(award)
                            # Most students only receive 1 or 2 scholarships per term
                            break

        return awards

    def _generate_payments_and_allocations(
        self,
        students: List[Student],
        invoices: List[Invoice],
        invoice_lines: List[InvoiceLine],
    ) -> Tuple[List[Payment], List[PaymentAllocation]]:
        payments = []
        allocations = []
        pay_counter = 1

        lines_by_inv = {}
        for l in invoice_lines:
            lines_by_inv.setdefault(l.invoice_id, []).append(l)

        # Group invoices by student
        invoices_by_student = {}
        for inv in invoices:
            invoices_by_student.setdefault(inv.student_id, []).append(inv)

        payment_methods = [
            PaymentMethod.ACH_TRANSFER,
            PaymentMethod.CREDIT_CARD,
            PaymentMethod.WIRE,
            PaymentMethod.THIRD_PARTY,
            PaymentMethod.CASH,
        ]
        method_weights = [0.45, 0.35, 0.12, 0.05, 0.03]

        for stu in students:
            stu_invoices = invoices_by_student.get(stu.student_id, [])
            for inv in stu_invoices:
                if inv.balance_due <= 0:
                    continue

                # Realistic payment scenarios:
                # 70% pay full balance, 20% partial payment, 5% overpay, 5% unpaid/late
                roll = self.rng.random()
                if roll < 0.05:
                    # Delinquent/unpaid - leave invoice open for late fee testing
                    continue

                pay_dt = (datetime.strptime(inv.issue_date, "%Y-%m-%d") + timedelta(days=self.rng.randint(5, 25))).strftime("%Y-%m-%d")

                if roll < 0.75:
                    # Full payment
                    pay_amt = inv.balance_due
                elif roll < 0.95:
                    # Partial payment (e.g. 50% or round amount)
                    pay_amt = round(inv.balance_due * self.rng.choice([0.30, 0.50, 0.65]), 2)
                else:
                    # Overpayment ($200 to $500 extra)
                    pay_amt = round(inv.balance_due + self.rng.uniform(100.0, 500.0), 2)

                if pay_amt <= 0:
                    continue

                pay_id = f"PAY-2026-{pay_counter:06d}"
                pay_counter += 1

                payment = Payment(
                    payment_id=pay_id,
                    student_id=stu.student_id,
                    term_id=inv.term_id,
                    payment_date=pay_dt,
                    payment_method=self.rng.choices(payment_methods, weights=method_weights)[0],
                    total_amount=pay_amt,
                    allocated_amount=0.0,
                    unallocated_amount=0.0,
                    status=PaymentStatus.SETTLED,
                    transaction_reference=f"TXN-{self.rng.randint(10000000, 99999999)}",
                )

                allocs = PaymentAllocator.allocate_payment(
                    payment=payment,
                    invoices=[inv],
                    invoice_lines_by_inv_id=lines_by_inv,
                    allocation_date=pay_dt,
                )
                payments.append(payment)
                allocations.extend(allocs)

        return payments, allocations

    def _generate_refunds(
        self,
        students: List[Student],
        payments: List[Payment],
        enrollments: List[Enrollment],
    ) -> List[Refund]:
        refunds = []
        ref_counter = 1

        payments_by_student = {}
        for p in payments:
            if p.status == PaymentStatus.SETTLED:
                payments_by_student.setdefault(p.student_id, []).append(p)

        # 3% of paid students have legitimate refunds (e.g. overpayment return or term drop)
        for stu in students:
            stu_payments = payments_by_student.get(stu.student_id, [])
            if not stu_payments:
                continue

            # Check if student has unallocated funds or withdrawal
            unallocated_pays = [p for p in stu_payments if p.unallocated_amount > 0]
            if unallocated_pays and self.rng.random() < 0.60:
                p = unallocated_pays[0]
                ref_amt = p.unallocated_amount
                ref_id = f"REF-2026-{ref_counter:06d}"
                ref_counter += 1

                refund, success = RefundManager.process_refund(
                    refund_id=ref_id,
                    student_id=stu.student_id,
                    payment=p,
                    term_id=p.term_id,
                    requested_amount=ref_amt,
                    reason=RefundReason.OVERPAYMENT,
                    request_date=p.payment_date,
                    all_student_payments=stu_payments,
                    existing_refunds=refunds,
                    approval_notes="Automatic return of unallocated credit balance.",
                )
                if success:
                    refunds.append(refund)

        return refunds

    def export_data(
        self,
        data: Dict[str, Any],
        output_dir: str = "data",
        formats: Tuple[str, ...] = ("csv", "json", "sqlite"),
    ) -> Dict[str, str]:
        """
        Exports generated datasets to CSV, JSON, and SQLite database.
        Returns a dictionary of file paths and their SHA-256 checksums.
        """
        os.makedirs(output_dir, exist_ok=True)
        manifest: Dict[str, str] = {}

        tables = {
            "students": [s.to_dict() for s in data["students"]],
            "programs": [p.to_dict() for p in data["programs"]],
            "fee_schedules": [fs.to_dict() for fs in data["fee_schedules"]],
            "enrollments": [e.to_dict() for e in data["enrollments"]],
            "invoices": [i.to_dict() for i in data["invoices"]],
            "invoice_lines": [il.to_dict() for il in data["invoice_lines"]],
            "scholarships": [s.to_dict() for s in data["scholarships"]],
            "eligibility_awards": [a.to_dict() for a in data["eligibility_awards"]],
            "payments": [p.to_dict() for p in data["payments"]],
            "allocations": [a.to_dict() for a in data["allocations"]],
            "refunds": [r.to_dict() for r in data["refunds"]],
            "ledger_entries": [l.to_dict() for l in data["ledger_entries"]],
        }

        # Step 7: Export Ground Truth separately (never leak into raw feature tables)
        gt_path = os.path.join(output_dir, "ground_truth.json")
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(data["ground_truth"], f, indent=2)
        manifest["ground_truth.json"] = self._compute_checksum(gt_path)

        # 1. Export CSV
        if "csv" in formats:
            csv_dir = os.path.join(output_dir, "csv")
            os.makedirs(csv_dir, exist_ok=True)
            for tbl_name, rows in tables.items():
                if not rows:
                    continue
                file_path = os.path.join(csv_dir, f"{tbl_name}.csv")
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)
                manifest[f"csv/{tbl_name}.csv"] = self._compute_checksum(file_path)

        # 2. Export JSON
        if "json" in formats:
            json_dir = os.path.join(output_dir, "json")
            os.makedirs(json_dir, exist_ok=True)
            for tbl_name, rows in tables.items():
                file_path = os.path.join(json_dir, f"{tbl_name}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(rows, f, indent=2)
                manifest[f"json/{tbl_name}.json"] = self._compute_checksum(file_path)

        # 3. Export SQLite
        if "sqlite" in formats:
            db_path = os.path.join(output_dir, "yottaflex_sfs.sqlite")
            if os.path.exists(db_path):
                os.remove(db_path)
            conn = sqlite3.connect(db_path)
            for tbl_name, rows in tables.items():
                if not rows:
                    continue
                cols = list(rows[0].keys())
                # Infer simple SQL types
                col_defs = []
                for c in cols:
                    val = rows[0][c]
                    if isinstance(val, int):
                        col_defs.append(f'"{c}" INTEGER')
                    elif isinstance(val, float):
                        col_defs.append(f'"{c}" REAL')
                    elif isinstance(val, bool):
                        col_defs.append(f'"{c}" BOOLEAN')
                    else:
                        col_defs.append(f'"{c}" TEXT')

                create_sql = f'CREATE TABLE IF NOT EXISTS "{tbl_name}" ({", ".join(col_defs)});'
                conn.execute(create_sql)

                placeholders = ", ".join(["?"] * len(cols))
                insert_sql = f'INSERT INTO "{tbl_name}" VALUES ({placeholders})'
                val_tuples = [tuple(r[c] for c in cols) for r in rows]
                conn.executemany(insert_sql, val_tuples)

            conn.commit()
            conn.close()
            manifest["yottaflex_sfs.sqlite"] = self._compute_checksum(db_path)

        return manifest

    @staticmethod
    def _compute_checksum(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        return sha256.hexdigest()
