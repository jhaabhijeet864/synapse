from core.engine.redaction import redact_sensitive_data

# test_redact_api_key
raw = "My OpenAI key is api_key = 'sk-abcdef123456789012345678'"
result = redact_sensitive_data(raw)
assert "[REDACTED_API_KEY]" in result, f'Expected REDACTED_API_KEY in {result}'
assert "sk-abcdef" not in result, f'sk-abcdef should be redacted in {result}'
print('test_redact_api_key PASSED')

# test_redact_db_uri
raw = "postgresql://admin:secretPass123@ep-cool.region.neon.tech/synapse"
result = redact_sensitive_data(raw)
assert "[REDACTED_DB_CONNECTION]" in result, f'Expected REDACTED_DB_CONNECTION in {result}'
assert "secretPass123" not in result, f'secretPass123 should be redacted in {result}'
print('test_redact_db_uri PASSED')

# test_redact_jwt
raw = "Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc123.def456"
result = redact_sensitive_data(raw)
assert "[REDACTED_JWT]" in result, f'Expected REDACTED_JWT in {result}'
assert "eyJ" not in result, f'eyJ should be redacted in {result}'
print('test_redact_jwt PASSED')

# test_redact_private_key
raw = "-----BEGIN RSA PRIVATE KEY-----MIIEpAIBAAKCAQEA---------------\n-----END RSA PRIVATE KEY-----"
result = redact_sensitive_data(raw)
assert "[REDACTED_PRIVATE_KEY]" in result, f'Expected REDACTED_PRIVATE_KEY in {result}'
assert "BEGIN RSA PRIVATE KEY" not in result, f'BEGIN RSA PRIVATE KEY should be redacted in {result}'
print('test_redact_private_key PASSED')

# test_redact_password
raw = "password: 'mySecretPass123'"
result = redact_sensitive_data(raw)
assert "[REDACTED_PASSWORD]" in result, f'Expected REDACTED_PASSWORD in {result}'
assert "mySecretPass123" not in result, f'mySecretPass123 should be redacted in {result}'
print('test_redact_password PASSED')

print('\nAll tests passed!')