***Domain Glossary***

User: a customer (default) or admin. Owns cart items and orders.

Category: groups products (1 category → many products).

Product: item for sale. Has price, stock, belongs to a category.

CartItem: represents a product in a user’s cart. (Your design: no Cart table, cart = all cart_items for user.)

Address: a delivery address owned by a user. One user can have many addresses; one is marked as default. Orders reference an address at the time of checkout.

Order: a purchase record created from cart. Has total_amount, status, payment_method, and a reference to the delivery address used at checkout.

OrderItem: snapshot of a product inside an order: price_at_time, quantity, subtotal.

InventoryChange: audit log of stock changes (+/-) with reason.

RefreshToken: auth domain; token per user session.

---

***Business Rules (MVP)***

Cart uniqueness: a user can have at most one cart_item per product (if adding again → increase quantity).

Quantity validity: cart/order quantities must be >= 1.

Stock rule: stock can never go below 0.

Checkout rule: an order can only be created if all cart items have enough stock.

Price snapshot: order_items.price_at_time must equal product price at checkout time (already in schema ✅).

Order immutability: after order is created, order_items should not change (except status transitions on order).

Admin-only: only admins can create/update/delete products.

Address ownership: a user can only checkout with an address that belongs to them.

Payment method: MVP supports COD (cash on delivery) only. Selected at checkout time and stored on the order.

Order status lifecycle (FSM): pending → confirmed → shipped → completed. Cancellation is a separate path (customer: pending only; admin: pending or confirmed).