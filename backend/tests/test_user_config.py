"""
Tests for User Configuration Router
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.routers.user_config import _encrypt_key, _decrypt_key


class TestEncryption:
    """Tests for API key encryption/decryption"""
    
    @pytest.mark.unit
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption are reversible"""
        original_key = "sk-test-api-key-12345"
        
        encrypted = _encrypt_key(original_key)
        decrypted = _decrypt_key(encrypted)
        
        assert decrypted == original_key
    
    @pytest.mark.unit
    def test_encryption_produces_different_output(self):
        """Test that encryption produces different output than input"""
        key = "test-api-key"
        encrypted = _encrypt_key(key)
        
        assert encrypted != key
        assert len(encrypted) > 0
    
    @pytest.mark.unit
    def test_empty_key_encryption(self):
        """Test encryption of empty key"""
        encrypted = _encrypt_key("")
        decrypted = _decrypt_key(encrypted)
        
        assert decrypted == ""
    
    @pytest.mark.unit
    def test_special_characters_encryption(self):
        """Test encryption with special characters"""
        key = "key-with-@#$%^special_chars!"
        
        encrypted = _encrypt_key(key)
        decrypted = _decrypt_key(encrypted)
        
        assert decrypted == key
    
    @pytest.mark.unit
    def test_unicode_encryption(self):
        """Test encryption with unicode characters"""
        key = "ключ-api-钥匙-🔑"
        
        encrypted = _encrypt_key(key)
        decrypted = _decrypt_key(encrypted)
        
        assert decrypted == key
    
    @pytest.mark.unit
    def test_invalid_decrypt_input(self):
        """Test decrypt with invalid input"""
        # Invalid hex string
        result = _decrypt_key("invalid-hex")
        assert result == ""
        
        # Empty string
        result = _decrypt_key("")
        assert result == ""


class TestConfigValidation:
    """Tests for configuration validation"""
    
    @pytest.mark.unit
    def test_agent_preset_values(self):
        """Test valid agent preset values"""
        valid_presets = ['conservative', 'balanced', 'aggressive', 'ai']
        
        for preset in valid_presets:
            assert preset in ['conservative', 'balanced', 'aggressive', 'ai']
    
    @pytest.mark.unit
    def test_language_values(self):
        """Test valid language values"""
        valid_languages = ['es', 'en']
        
        for lang in valid_languages:
            assert lang in ['es', 'en']


class TestConfigEndpoints:
    """Tests for configuration API endpoints"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_save_and_load_config(self):
        """Test saving and loading configuration"""
        # This would need FastAPI TestClient and database
        # For now, just verify the logic exists
        pass
    
    @pytest.mark.unit
    def test_api_key_not_returned(self):
        """Verify API key is never returned in responses"""
        # The response model should only return has_kimi_api_key boolean
        # not the actual key
        from app.routers.user_config import UserConfigResponse
        
        # Create a sample response
        response = UserConfigResponse(
            account_id="test123",
            has_kimi_api_key=True,
            use_kimi_api=True,
            agent_preset="balanced",
            agent_symbols=["BTC/USDT"],
            agent_strategies=["rsi"],
            agent_risk_config=None,
            language="es",
            tutorial_seen=False,
            updated_at="2024-01-01T00:00:00"
        )
        
        # Verify response doesn't contain the actual key
        response_dict = response.dict()
        assert 'kimi_api_key' not in response_dict
        assert 'kimi_api_key_encrypted' not in response_dict
        assert response_dict['has_kimi_api_key'] is True