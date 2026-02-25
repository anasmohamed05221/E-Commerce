***Domain Glossary***

User: a customer (default) or admin. Owns cart items and orders.

Category: groups products (1 category → many products).

Product: item for sale. Has price, stock, belongs to a category.

CartItem: represents a product in a user’s cart. (Your design: no Cart table, cart = all cart_items for user.)

Order: a purchase record created from cart. Has total_amount + status.

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