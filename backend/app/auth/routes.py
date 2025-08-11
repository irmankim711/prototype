from flask import request, jsonify, make_response, current_app
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

    # ✅ FIXED: Using proper SQLAlchemy instantiation
    user = User()  # Create instance first
    user.email = email
    user.first_name = payload.get("first_name", "")
    user.last_name = payload.get("last_name", "")
    user.username = payload.get("username", "").strip() or None  # Convert empty to None
    user.phone = payload.get("phone", "")
    user.company = payload.get("company", "")
    user.job_title = payload.get("job_title", "")
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
        
        # Set cookies with proper security settings
        resp.set_cookie(
            "access_token_cookie", 
            access_token, 
            httponly=True, 
            secure=False,  # Set to True in production with HTTPS
            samesite="Lax"
        )
        resp.set_cookie(
            "refresh_token_cookie", 
            refresh_token, 
            httponly=True, 
            secure=False,  # Set to True in production with HTTPS
            samesite="Lax",
            path="/api/auth/refresh"
        )
        
        return resp
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Login error: {str(e)}")
        print(f"Full traceback: {error_details}")
        current_app.logger.error(f"Login failed: {str(e)} - {error_details}")
        return jsonify({"msg": "Internal server error", "error": str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        print(f"Refresh endpoint called")
        print(f"Request cookies: {request.cookies}")
        print(f"Request headers: {dict(request.headers)}")
        
        # Get refresh token from cookie - Flask-JWT-Extended handles this automatically
        # when JWT_TOKEN_LOCATION includes 'cookies'
        current_user = get_jwt_identity()
        print(f"Current user from JWT: {current_user}")
        
        if not current_user:
            print("No user identity found in refresh token")
            return jsonify({"msg": "Invalid refresh token"}), 401
        
        # Create new access token
        new_token = create_access_token(identity=current_user)
        print(f"Generated new access token for user: {current_user}")
        
        return jsonify({"access_token": new_token}), 200
        
    except Exception as e:
        print(f"Refresh error: {str(e)}")
        print(f"Error type: {type(e)}")
        
        # Provide specific error messages
        if "Missing Authorization Header" in str(e):
            return jsonify({"msg": "No refresh token provided"}), 401
        elif "token has expired" in str(e).lower():
            return jsonify({"msg": "Refresh token expired"}), 401
        elif "Invalid token" in str(e):
            return jsonify({"msg": "Invalid refresh token"}), 401
        else:
            return jsonify({"msg": "Token refresh failed", "error": str(e)}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify({"id": user.id, "email": user.email, "is_active": user.is_active})
