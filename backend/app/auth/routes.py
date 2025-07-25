from flask import request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from .. import db
from ..models import User
from . import auth_bp

@auth_bp.route('/register', methods=['POST'])
def register():
    """Create a new user account."""
    payload = request.get_json(force=True)
    email = (payload.get("email") or "").lower().strip()
    password = payload.get("password")

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already registered"}), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "Registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        payload = request.get_json(force=True)
        email = (payload.get("email") or "").lower().strip()
        password = payload.get("password")

        if not email or not password:
            return jsonify({"msg": "Email and password are required"}), 400

        user: User | None = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"msg": "Invalid credentials"}), 401
            
        if not user.check_password(password):
            return jsonify({"msg": "Invalid credentials"}), 401

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        resp = make_response(jsonify({
            "access_token": access_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }), 200)
        
        # Set cookies
        resp.set_cookie("access_token_cookie", access_token, httponly=True, samesite="Lax")
        resp.set_cookie("refresh_token", refresh_token, httponly=True, samesite="Lax", path="/api/auth/refresh")
        
        return resp
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"msg": "Internal server error"}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify({"access_token": new_token})

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify({"id": user.id, "email": user.email, "is_active": user.is_active})
