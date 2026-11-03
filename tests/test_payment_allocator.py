"""
Tests for Payment Allocation Engine.
"""

import unittest
from yottaflex.models.enums import PaymentMethod, PaymentStatus, InvoiceStatus, AllocationStatus
from yottaflex.models.entities import Payment, Invoice
from yottaflex.engine.payment_allocator import PaymentAllocator


class TestPaymentAllocator(unittest.TestCase):

    def test_full_payment_allocation(self):
        invoice = Invoice("INV-01", "STU-01", "ENR-01", "TERM-2026-FALL", "2026-08-15", "2026-09-15", subtotal_amount=5000.0, balance_due=5000.0)
        payment = Payment("PAY-01", "STU-01", "TERM-2026-FALL", "2026-08-20", PaymentMethod.ACH_TRANSFER, total_amount=5000.0)

        allocs = PaymentAllocator.allocate_payment(payment, [invoice])

        self.assertEqual(len(allocs), 1)
        self.assertEqual(allocs[0].allocated_amount, 5000.0)
        self.assertEqual(invoice.balance_due, 0.0)
        self.assertEqual(invoice.status, InvoiceStatus.PAID)
        self.assertEqual(payment.allocated_amount, 5000.0)
        self.assertEqual(payment.unallocated_amount, 0.0)

    def test_partial_payment_allocation(self):
        invoice = Invoice("INV-02", "STU-02", "ENR-02", "TERM-2026-FALL", "2026-08-15", "2026-09-15", subtotal_amount=5000.0, balance_due=5000.0)
        payment = Payment("PAY-02", "STU-02", "TERM-2026-FALL", "2026-08-20", PaymentMethod.CREDIT_CARD, total_amount=2000.0)

        allocs = PaymentAllocator.allocate_payment(payment, [invoice])

        self.assertEqual(len(allocs), 1)
        self.assertEqual(allocs[0].allocated_amount, 2000.0)
        self.assertEqual(invoice.balance_due, 3000.0)
        self.assertEqual(invoice.status, InvoiceStatus.PARTIALLY_PAID)
        self.assertEqual(payment.allocated_amount, 2000.0)
        self.assertEqual(payment.unallocated_amount, 0.0)

    def test_overpayment_credit_balance(self):
        invoice = Invoice("INV-03", "STU-03", "ENR-03", "TERM-2026-FALL", "2026-08-15", "2026-09-15", subtotal_amount=4000.0, balance_due=4000.0)
        payment = Payment("PAY-03", "STU-03", "TERM-2026-FALL", "2026-08-20", PaymentMethod.WIRE, total_amount=4500.0)

        allocs = PaymentAllocator.allocate_payment(payment, [invoice])

        self.assertEqual(len(allocs), 1)
        self.assertEqual(allocs[0].allocated_amount, 4000.0)
        self.assertEqual(invoice.balance_due, 0.0)
        self.assertEqual(invoice.status, InvoiceStatus.PAID)
        self.assertEqual(payment.allocated_amount, 4000.0)
        self.assertEqual(payment.unallocated_amount, 500.00)  # excess credit balance

    def test_multi_invoice_fifo_allocation(self):
        inv1 = Invoice("INV-A", "STU-04", "ENR-04", "TERM-2026-FALL", "2026-08-01", "2026-09-01", subtotal_amount=2000.0, balance_due=2000.0)
        inv2 = Invoice("INV-B", "STU-04", "ENR-05", "TERM-2026-FALL", "2026-08-15", "2026-09-15", subtotal_amount=3000.0, balance_due=3000.0)
        payment = Payment("PAY-04", "STU-04", "TERM-2026-FALL", "2026-08-20", PaymentMethod.ACH_TRANSFER, total_amount=3500.0)

        allocs = PaymentAllocator.allocate_payment(payment, [inv1, inv2])

        # FIFO: inv1 settled completely ($2000), remainder ($1500) applied to inv2
        self.assertEqual(len(allocs), 2)
        self.assertEqual(allocs[0].invoice_id, "INV-A")
        self.assertEqual(allocs[0].allocated_amount, 2000.0)
        self.assertEqual(inv1.balance_due, 0.0)
        self.assertEqual(inv1.status, InvoiceStatus.PAID)

        self.assertEqual(allocs[1].invoice_id, "INV-B")
        self.assertEqual(allocs[1].allocated_amount, 1500.0)
        self.assertEqual(inv2.balance_due, 1500.0)
        self.assertEqual(inv2.status, InvoiceStatus.PARTIALLY_PAID)


if __name__ == "__main__":
    unittest.main()
