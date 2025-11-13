"""
Google Forms Empty Responses Diagnostic Tool
This script identifies why the Google Forms API returns empty responses
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.production.user_models import UserToken, User
from app.services.production.google_forms_service import google_forms_service
import logging
import requests

# Enable detailed logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = create_app()

def check_oauth_user(user_id: int):
    """Check which Google account is authenticated"""
    logger.info("="*80)
    logger.info("STEP 1: CHECKING AUTHENTICATED GOOGLE ACCOUNT")
    logger.info("="*80)

    with app.app_context():
        # Check database for Google token
        user_token = UserToken.query.filter_by(
            user_id=user_id,
            platform='google',
            is_active=True
        ).first()

        if not user_token:
            logger.error(f"❌ No Google OAuth token found for user_id={user_id}")
            logger.error("   User needs to authenticate via OAuth flow")
            logger.error("   Go to your app and click 'Connect Google Forms'")
            return None

        logger.info(f"✅ Found Google OAuth token for user_id={user_id}")
        logger.info(f"   Platform User ID: {user_token.platform_user_id}")
        logger.info(f"   Token issued: {user_token.issued_at}")
        logger.info(f"   Token expires: {user_token.expires_at}")
        logger.info(f"   Token valid: {user_token.is_valid()}")
        logger.info(f"   Scopes: {user_token.scopes}")

        # Get credentials and check token info
        credentials = google_forms_service.get_credentials(user_id)
        if credentials and credentials.token:
            try:
                response = requests.get(
                    'https://www.googleapis.com/oauth2/v1/tokeninfo',
                    params={'access_token': credentials.token}
                )
                if response.status_code == 200:
                    token_info = response.json()
                    logger.info(f"\n📧 AUTHENTICATED AS: {token_info.get('email', 'Unknown')}")
                    logger.info(f"   User ID: {token_info.get('user_id', 'Unknown')}")
                    logger.info(f"   Verified Email: {token_info.get('verified_email', False)}")
                    logger.info(f"   Token expires in: {token_info.get('expires_in', 0)} seconds")
                    return token_info.get('email')
                else:
                    logger.warning(f"⚠️ Could not verify token: {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ Error checking token info: {str(e)}")

        return user_token.platform_user_id


def test_form_access(user_id: int, form_id: str):
    """Test if user can access form responses"""
    logger.info("\n" + "="*80)
    logger.info("STEP 2: TESTING GOOGLE FORMS API ACCESS")
    logger.info("="*80)

    with app.app_context():
        try:
            # Test fetching form structure
            logger.info(f"\n🔍 Testing form access for form_id={form_id}")

            result = google_forms_service.get_form_responses(user_id, form_id)

            logger.info("\n" + "="*80)
            logger.info("RESULT")
            logger.info("="*80)
            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Form Title: {result.get('form_title', 'N/A')}")
            logger.info(f"Response Count: {result.get('response_count', 0)}")

            if result.get('response_count', 0) == 0:
                logger.warning("\n⚠️ ZERO RESPONSES RETURNED!")
                logger.warning("\nPossible causes:")
                logger.warning("  1. ❌ Authenticated user doesn't OWN the form")
                logger.warning("  2. ❌ Form ID is incorrect")
                logger.warning("  3. ❌ Form genuinely has no responses")
                logger.warning("  4. ❌ Form sharing permissions are wrong")

                logger.info("\n" + "="*80)
                logger.info("DIAGNOSIS")
                logger.info("="*80)
                logger.info("The Google Forms API only returns responses for:")
                logger.info("  ✅ Forms OWNED by the authenticated user")
                logger.info("  ✅ Forms where authenticated user has EDITOR access")
                logger.info("  ❌ NOT for forms with VIEW-ONLY access")

            else:
                logger.info(f"\n✅ SUCCESS! Found {result.get('response_count')} responses")
                if result.get('responses'):
                    first_response = result['responses'][0]
                    logger.info("\nSample response:")
                    logger.info(f"  Response ID: {first_response.get('response_id')}")
                    logger.info(f"  Timestamp: {first_response.get('create_time')}")
                    logger.info(f"  Answer count: {len(first_response.get('answers', {}))}")

            return result

        except Exception as e:
            logger.error(f"\n❌ ERROR: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None


def provide_solutions(authenticated_email: str, form_id: str):
    """Provide step-by-step solutions"""
    logger.info("\n" + "="*80)
    logger.info("STEP 3: SOLUTIONS")
    logger.info("="*80)

    logger.info(f"\nAuthenticated Google Account: {authenticated_email}")
    logger.info(f"Form ID: {form_id}")

    logger.info("\n📋 SOLUTION OPTIONS:")
    logger.info("\n1️⃣  OPTION A: Share the form with the authenticated account")
    logger.info(f"   • Open the Google Form in browser")
    logger.info(f"   • Click the ⋮ (three dots) menu")
    logger.info(f"   • Click 'Add collaborators'")
    logger.info(f"   • Add: {authenticated_email}")
    logger.info(f"   • Set permission to: EDITOR (NOT viewer)")
    logger.info(f"   • Click 'Send'")

    logger.info("\n2️⃣  OPTION B: Re-authenticate with form owner account")
    logger.info(f"   • Go to your app")
    logger.info(f"   • Disconnect Google Forms")
    logger.info(f"   • Reconnect using the Google account that OWNS the form")

    logger.info("\n3️⃣  OPTION C: Transfer form ownership")
    logger.info(f"   • Open Google Forms as current owner")
    logger.info(f"   • Share with {authenticated_email}")
    logger.info(f"   • Make them a co-owner or transfer ownership")

    logger.info("\n" + "="*80)


if __name__ == "__main__":
    logger.info("Google Forms Empty Responses Diagnostic Tool")
    logger.info("=" * 80)

    # Get parameters
    if len(sys.argv) < 3:
        logger.error("Usage: python diagnose_google_forms.py <user_id> <form_id>")
        logger.error("\nExample:")
        logger.error("  python diagnose_google_forms.py 1 1yxEBr9G123ABC-xyz")
        logger.error("\nTo find your form_id:")
        logger.error("  URL: https://docs.google.com/forms/d/1yxEBr9G123ABC-xyz/edit")
        logger.error("                                      ^^^^^^^^^^^^^^^^^^^")
        logger.error("                                      This is the form_id")
        sys.exit(1)

    user_id = int(sys.argv[1])
    form_id = sys.argv[2]

    # Run diagnostics
    authenticated_email = check_oauth_user(user_id)

    if authenticated_email:
        result = test_form_access(user_id, form_id)
        provide_solutions(authenticated_email, form_id)

    logger.info("\n" + "="*80)
    logger.info("DIAGNOSTIC COMPLETE")
    logger.info("="*80)
    logger.info("\nNext steps:")
    logger.info("  1. Note the authenticated email above")
    logger.info("  2. Check who owns the Google Form")
    logger.info("  3. Follow one of the solution options")
    logger.info("  4. Re-run this script to verify the fix")
