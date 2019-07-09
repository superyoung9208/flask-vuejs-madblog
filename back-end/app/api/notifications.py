"""
File:notifications.py
Author:Young
"""
from flask import g, jsonify
from flask import request

from app.api.auth import token_auth
from app.api.error import error_response
from app.models import Notification
from . import bp


@bp.route('notifications/<int:id>', methods=["GET"])
@token_auth.login_required
def get_notification(id):
    notification = Notification.query.get_or_404(id)
    if g.current_user != notification.user:
        return error_response(403)
    data = notification.to_dict()
    return jsonify(data)
