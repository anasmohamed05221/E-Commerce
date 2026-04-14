**Business Rules**

---

**Cart**

- One cart item per product per user. Adding the same product again increments quantity.
- Quantity must be ≥ 1.
- Cart item quantity cannot exceed current product stock (enforced on add and update).
- Cart is cleared atomically on successful checkout.

---

**Checkout**

- Cart must be non-empty to checkout.
- Each item's quantity must not exceed available stock. Checked twice: once before the transaction, once inside with SELECT FOR UPDATE to prevent race conditions.
- Address used at checkout must belong to the user.
- Product price is snapshotted at checkout time (`price_at_time`). Price changes never retroactively affect existing orders.
- Payment method is COD (cash on delivery) only. *(MVP — Stripe added in Epic 2)*
- Stock is decremented at checkout (not reserved). *(MVP — Epic 2 will reserve stock on Stripe checkout creation and confirm on payment webhook)*
- Checkout is atomic: order creation, order items, stock decrement, inventory log, and cart clear all commit together or all roll back.
- Every stock decrement is logged as an `InventoryChange` with reason `SALE`.

---

**Orders**

- Status follows a strict FSM: `PENDING → CONFIRMED → SHIPPED → COMPLETED`. No skipping, no reversals.
- `COMPLETED` and `CANCELLED` are terminal states — no transitions out.
- Customer can only cancel `PENDING` orders.
- Admin can cancel `PENDING` or `CONFIRMED` orders.
- Cancellation restores stock and logs an `InventoryChange` with reason `CANCELLATION`. Product rows are locked in sorted order (by product_id) to prevent deadlocks.
- Order items are immutable after creation.

---

**Auth**

- Email must be unique.
- Email must be verified (6-digit code, 10-min expiry) before login is permitted.
- Inactive accounts cannot log in.
- Password reset: token is time-limited (15 min), hashed (SHA-256), single-use. Unknown emails return silently — no user enumeration.
- Password reset revokes all sessions.
- Password change (authenticated): two-step flow. Current password is verified, pending hash stored, confirmation email sent. Token expires in 15 min. On confirm: hash applied, all sessions revoked. On deny: pending hash cleared, all sessions revoked, security alert sent.
- Token rotation: every refresh revokes the old token and issues a new pair. Presenting a revoked token is rejected.

---

**Addresses**

- Users can only access and use addresses they own.
- Only one default address per user at a time. Setting a new default clears the previous one.
- First address created is automatically set as default.

---

**Users**

- Account deactivation (self): requires password confirmation. Sets `is_active=False`, revokes all sessions. Data is preserved (soft delete).
- Admin cannot deactivate or change the role of their own account.
- Admin can reactivate deactivated users.

---

**Products & Inventory**

- Only admins can create, update, or delete products.
- Stock never goes below 0.
- Every stock change (sale, cancellation, restock, adjustment, return) is logged in `inventory_changes` with a reason.