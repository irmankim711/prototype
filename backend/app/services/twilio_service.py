import os
from twilio.rest import Client
import logging

class TwilioService:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.verify_service_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')
        
        if not all([self.account_sid, self.auth_token]):
            print("Twilio credentials not properly configured")
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                print("Twilio client initialized successfully")
                if self.verify_service_sid:
                    print(f"Twilio Verify service configured: {self.verify_service_sid}")
            except Exception as e:
                print(f"Failed to initialize Twilio client: {e}")
                self.client = None
    
    def send_verification_code(self, to_phone):
        """
        Send verification code using Twilio Verify
        
        Args:
            to_phone (str): Recipient phone number (with country code)
            
        Returns:
            dict: Success/error response
        """
        if not self.client or not self.verify_service_sid:
            return {
                'success': False,
                'error': 'Twilio Verify service not configured'
            }
        
        try:
            # Ensure phone number has country code
            if not to_phone.startswith('+'):
                # Assume Malaysian number if no country code
                to_phone = '+60' + to_phone.lstrip('0')
            
            # Clean phone number
            to_phone = to_phone.replace(' ', '').replace('-', '')
            
            # Send verification code using Verify
            verification = self.client.verify \
                .v2 \
                .services(self.verify_service_sid) \
                .verifications \
                .create(to=to_phone, channel='sms')
            
            print(f"Verification code sent successfully to {to_phone}. SID: {verification.sid}")
            
            return {
                'success': True,
                'verification_sid': verification.sid,
                'status': verification.status,
                'to': to_phone
            }
            
        except Exception as e:
            print(f"Failed to send verification code to {to_phone}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_code(self, to_phone, code):
        """
        Verify the code using Twilio Verify
        
        Args:
            to_phone (str): Phone number that received the code
            code (str): Verification code to check
            
        Returns:
            dict: Success/error response
        """
        if not self.client or not self.verify_service_sid:
            return {
                'success': False,
                'error': 'Twilio Verify service not configured'
            }
        
        try:
            # Ensure phone number has country code
            if not to_phone.startswith('+'):
                # Assume Malaysian number if no country code
                to_phone = '+60' + to_phone.lstrip('0')
            
            # Clean phone number
            to_phone = to_phone.replace(' ', '').replace('-', '')
            
            # Verify the code
            verification_check = self.client.verify \
                .v2 \
                .services(self.verify_service_sid) \
                .verification_checks \
                .create(to=to_phone, code=code)
            
            print(f"Verification check result for {to_phone}: {verification_check.status}")
            
            return {
                'success': verification_check.status == 'approved',
                'status': verification_check.status,
                'to': to_phone
            }
            
        except Exception as e:
            print(f"Failed to verify code for {to_phone}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_sms(self, to_phone, message):
        """
        Send regular SMS (legacy method)
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Twilio client not initialized'
            }
        
        try:
            if not to_phone.startswith('+'):
                to_phone = '+60' + to_phone.lstrip('0')
            
            message_instance = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_phone
            )
            
            return {
                'success': True,
                'message_sid': message_instance.sid,
                'status': message_instance.status
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_otp_sms(self, to_phone, otp_code):
        """
        Legacy method - prefer send_verification_code() for Verify service
        """
        message = f"Your StratoSys verification code is: {otp_code}. This code will expire in 10 minutes."
        return self.send_sms(to_phone, message)
    
    def is_configured(self):
        """Check if Twilio is properly configured"""
        return self.client is not None
    
    def is_verify_configured(self):
        """Check if Twilio Verify is properly configured"""
        return self.client is not None and self.verify_service_sid is not None

# Initialize Twilio service
twilio_service = TwilioService()
