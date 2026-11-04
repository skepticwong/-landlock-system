# backend/utils/notifications.py
"""
In-app notification system for LandLock.

Notifications are created whenever a transaction state change requires
action from another party. They show up in the system navbar bell and
can be viewed / marked as read from the dropdown panel.
"""

from datetime import datetime
from db.sqlite_db import db


# ──────────────────────────────────────────────────────
# Core helpers
# ──────────────────────────────────────────────────────

def create_notification(user_id: int, type_: str, title: str,
                        message: str, link: str = None) -> dict | None:
    """
    Create an in-app notification for a user.

    type_ values:
      - pending_approval   : You need to approve something
      - buyer_confirm      : Buyer needs to confirm
      - approved           : Someone approved
      - rejected           : Someone rejected
      - completed          : Transaction completed
      - ownership_changed  : Plot ownership transferred
    """
    return db.insert("notifications", {
        "user_id": user_id,
        "type": type_,
        "title": title,
        "message": message,
        "link": link or "/transactions/approvals",
        "is_read": 0,
        "created_at": datetime.now().isoformat(),
    })


def get_user_notifications(user_id: int, limit: int = 30) -> list:
    """Return the user's most recent notifications (newest first)."""
    return db.select(
        "notifications",
        eq={"user_id": user_id},
        order="created_at DESC",
    )[:limit]


def get_unread_count(user_id: int) -> int:
    """Return the number of unread notifications for a user."""
    rows = db.select(
        "notifications",
        columns="COUNT(*) as cnt",
        eq={"user_id": user_id, "is_read": 0},
    )
    return rows[0]["cnt"] if rows else 0


def mark_read(notification_id: int, user_id: int) -> bool:
    """Mark a single notification as read (scoped to user)."""
    db.update(
        "notifications",
        {"is_read": 1},
        eq={"id": notification_id, "user_id": user_id},
    )
    return True


def mark_all_read(user_id: int) -> bool:
    """Mark all of a user's notifications as read."""
    db.update(
        "notifications",
        {"is_read": 1},
        eq={"user_id": user_id, "is_read": 0},
    )
    return True


# ──────────────────────────────────────────────────────
# High-level notification triggers
# ──────────────────────────────────────────────────────

def notify_buyer_to_confirm(buyer_id: int, seller_name: str,
                            plot_name: str, tx_id: int):
    """Called when a seller initiates a sale — buyer must confirm."""
    create_notification(
        user_id=buyer_id,
        type_="buyer_confirm",
        title="New Purchase Awaiting Your Confirmation",
        message=f"{seller_name} has initiated a sale of {plot_name} to you. "
                "Please confirm the purchase.",
        link=f"/transactions/approvals",
    )


def notify_chief_to_approve(chief_id: int, seller_name: str,
                            buyer_name: str, plot_name: str, tx_id: int):
    """Called after buyer confirms — chief needs to approve."""
    create_notification(
        user_id=chief_id,
        type_="pending_approval",
        title="Land Sale Awaiting Your Approval",
        message=f"A sale of {plot_name} from {seller_name} to {buyer_name} "
                "requires your approval as chief.",
        link="/transactions/approvals",
    )


def notify_witness_to_approve(witness_id: int, seller_name: str,
                              buyer_name: str, plot_name: str, tx_id: int):
    """Called after buyer confirms — witness needs to approve."""
    create_notification(
        user_id=witness_id,
        type_="pending_approval",
        title="Land Sale Awaiting Your Approval",
        message=f"A sale of {plot_name} from {seller_name} to {buyer_name} "
                "requires your approval as witness.",
        link="/transactions/approvals",
    )


def notify_parties_approved(tx: dict, approver_name: str, role: str):
    """Called when chief or witness approves — notify seller & buyer of progress."""
    plot_name = tx.get("plot_name", f"Plot #{tx.get('plot_id', '?')}")
    for uid in {tx.get("seller_id"), tx.get("buyer_id")}:
        if uid:
            create_notification(
                user_id=uid,
                type_="approved",
                title=f"{role.title()} Approved Sale",
                message=f"{approver_name} ({role}) has approved the sale of {plot_name}.",
                link="/transactions",
            )


def notify_all_parties_completed(tx: dict):
    """Called when all approvals are in and ownership is transferred."""
    plot_name = tx.get("plot_name", f"Plot #{tx.get('plot_id', '?')}")
    buyer_name = tx.get("buyer_name", "the buyer")
    amount = tx.get("amount", 0)
    amount_str = f"MK {amount:,.0f}" if amount else ""

    # Seller — ownership has left their hands
    if tx.get("seller_id"):
        create_notification(
            user_id=tx["seller_id"],
            type_="completed",
            title="Sale Completed — Ownership Transferred",
            message=f"The sale of {plot_name} to {buyer_name} for {amount_str} "
                    "is now complete. Ownership has been transferred.",
            link="/transactions",
        )

    # Buyer — they now own the plot
    if tx.get("buyer_id"):
        create_notification(
            user_id=tx["buyer_id"],
            type_="completed",
            title="Purchase Completed — You Now Own This Land",
            message=f"Your purchase of {plot_name} for {amount_str} is complete. "
                    "Ownership has been transferred to you.",
            link="/transactions",
        )

    # Chief and witness — just a heads-up that the deal closed
    for uid in {tx.get("chief_id"), tx.get("witness_id")}:
        if uid:
            create_notification(
                user_id=uid,
                type_="completed",
                title="Sale Completed",
                message=f"The sale of {plot_name} has been completed. "
                        "Thank you for your oversight.",
                link="/transactions",
            )


def notify_all_parties_rejected(tx: dict, rejector_role: str, reason: str):
    """Called when any party rejects the transaction."""
    plot_name = tx.get("plot_name", f"Plot #{tx.get('plot_id', '?')}")
    reason_str = f" Reason: {reason}" if reason else ""

    for uid in {tx.get("seller_id"), tx.get("buyer_id"),
                tx.get("chief_id"), tx.get("witness_id")}:
        if uid:
            create_notification(
                user_id=uid,
                type_="rejected",
                title="Sale Rejected",
                message=f"The sale of {plot_name} was rejected by the "
                        f"{rejector_role}.{reason_str}",
                link="/transactions",
            )
