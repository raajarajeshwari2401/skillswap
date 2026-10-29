"""Wallet blueprint: Points balance and immutable transaction ledger."""

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models.wallet import PointTransaction

wallet_bp = Blueprint("wallet", __name__, url_prefix="/wallet")


@wallet_bp.route("/")
@login_required
def overview():
    """Display user wallet balance, escrow breakdown, and transaction ledger."""
    wallet = current_user.wallet
    filter_type = request.args.get("type", "all")

    tx_query = wallet.transactions

    if filter_type == "earnings":
        tx_query = tx_query.filter_by(transaction_type="session_earning")
    elif filter_type == "payments":
        tx_query = tx_query.filter_by(transaction_type="session_payment")
    elif filter_type == "escrow":
        tx_query = tx_query.filter(PointTransaction.transaction_type.in_(["hold_reservation", "release_reservation"]))
    elif filter_type == "bonuses":
        tx_query = tx_query.filter_by(transaction_type="welcome_bonus")

    transactions = tx_query.all()

    return render_template(
        "wallet/index.html",
        wallet=wallet,
        transactions=transactions,
        current_filter=filter_type,
    )
