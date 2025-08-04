"""
Unit tests for authentication utilities.
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from crud.user import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_token
)
from auth import Settings


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test password hashing creates different hashes for same password."""
        password = "testpassword123"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        assert len(hash1) > 20  # Reasonable hash length
        assert len(hash2) > 20
    
    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_empty_password_handling(self):
        """Test handling of empty passwords."""
        empty_password = ""
        hashed = get_password_hash(empty_password)
        
        assert verify_password(empty_password, hashed) is True
        assert verify_password("nonempty", hashed) is False
    
    def test_special_characters_in_password(self):
        """Test passwords with special characters."""
        special_password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = get_password_hash(special_password)
        
        assert verify_password(special_password, hashed) is True
        assert verify_password("different", hashed) is False
    
    def test_unicode_password(self):
        """Test passwords with unicode characters."""
        unicode_password = "pássw∅rd123🔒"
        hashed = get_password_hash(unicode_password)
        
        assert verify_password(unicode_password, hashed) is True
        assert verify_password("password123", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 20  # JWT tokens are longer
        
        # Token should have 3 parts separated by dots
        parts = token.split('.')
        assert len(parts) == 3
    
    def test_create_token_with_expiration(self):
        """Test token creation with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires_delta)
        
        assert isinstance(token, str)
        
        # Decode token to check expiration
        settings = Settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        exp = payload.get("exp")
        assert exp is not None
        
        # Check that expiration is approximately 30 minutes from now
        exp_datetime = datetime.fromtimestamp(exp)
        expected_exp = datetime.utcnow() + expires_delta
        
        # Allow 5 second tolerance
        assert abs((exp_datetime - expected_exp).total_seconds()) < 5
    
    def test_verify_valid_token(self):
        """Test verification of valid token."""
        data = {"sub": "testuser", "role": "customer"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["role"] == "customer"
        assert "exp" in payload
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.jwt.token"
        
        payload = verify_token(invalid_token)
        assert payload is None
    
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        data = {"sub": "testuser"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires_delta)
        
        payload = verify_token(token)
        assert payload is None
    
    def test_verify_token_wrong_signature(self):
        """Test verification of token with wrong signature."""
        # Create token with different secret
        settings = Settings()
        wrong_secret = "wrong_secret_key"
        
        data = {"sub": "testuser"}
        exp = datetime.utcnow() + timedelta(minutes=15)
        data.update({"exp": exp})
        
        token = jwt.encode(data, wrong_secret, algorithm=settings.algorithm)
        
        payload = verify_token(token)
        assert payload is None
    
    def test_token_includes_required_claims(self):
        """Test that tokens include required claims."""
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert payload["role"] == "admin"
    
    def test_token_with_additional_data(self):
        """Test token creation with additional custom data."""
        data = {
            "sub": "testuser",
            "role": "admin",
            "user_id": 123,
            "permissions": ["read", "write"]
        }
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
        assert payload["user_id"] == 123
        assert payload["permissions"] == ["read", "write"]


class TestAuthSettings:
    """Test authentication settings."""
    
    def test_settings_initialization(self):
        """Test that settings are properly initialized."""
        settings = Settings()
        
        assert settings.secret_key
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes > 0
        assert len(settings.secret_key) >= 32  # Reasonable key length
    
    def test_settings_immutable_after_creation(self):
        """Test that critical settings can't be easily modified."""
        settings = Settings()
        original_secret = settings.secret_key
        
        # These shouldn't affect the actual settings
        settings.secret_key = "new_secret"
        settings.algorithm = "RS256"
        
        # Create new instance to verify original settings
        new_settings = Settings()
        assert new_settings.secret_key == original_secret
        assert new_settings.algorithm == "HS256"


class TestSecurityEdgeCases:
    """Test security edge cases and potential vulnerabilities."""
    
    def test_none_algorithm_attack_prevention(self):
        """Test that 'none' algorithm attack is prevented."""
        # Try to create a token with 'none' algorithm
        data = {"sub": "attacker"}
        
        settings = Settings()
        
        # Create token with 'none' algorithm (attack attempt)
        malicious_token = jwt.encode(data, "", algorithm="none")
        
        # Verification should fail
        payload = verify_token(malicious_token)
        assert payload is None
    
    def test_key_confusion_prevention(self):
        """Test prevention of key confusion attacks."""
        # This test ensures we're not vulnerable to using public keys as secrets
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Token should not be verifiable with empty key
        try:
            payload = jwt.decode(token, "", algorithms=["HS256"])
            assert False, "Token should not be verifiable with empty key"
        except JWTError:
            pass  # Expected
    
    def test_timing_attack_resistance(self):
        """Test that password verification is resistant to timing attacks."""
        import time
        
        password = "testpassword"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        # Time correct password verification
        start = time.time()
        verify_password(password, hashed)
        correct_time = time.time() - start
        
        # Time incorrect password verification
        start = time.time()
        verify_password(wrong_password, hashed)
        incorrect_time = time.time() - start
        
        # Times should be roughly similar (within 50ms)
        time_diff = abs(correct_time - incorrect_time)
        assert time_diff < 0.05, "Password verification may be vulnerable to timing attacks"
    
    def test_password_hash_entropy(self):
        """Test that password hashes have sufficient entropy."""
        password = "testpassword"
        hashes = set()
        
        # Generate multiple hashes of the same password
        for _ in range(100):
            hash_value = get_password_hash(password)
            hashes.add(hash_value)
        
        # All hashes should be unique due to salt
        assert len(hashes) == 100, "Password hashes should be unique due to salting"
    
    def test_token_tampering_detection(self):
        """Test that token tampering is detected."""
        data = {"sub": "testuser", "role": "customer"}
        token = create_access_token(data)
        
        # Tamper with the token
        parts = token.split('.')
        
        # Modify payload (second part)
        tampered_token = f"{parts[0]}.{parts[1]}modified.{parts[2]}"
        
        payload = verify_token(tampered_token)
        assert payload is None, "Tampered token should not be valid"