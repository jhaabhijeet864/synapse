from core.engine.redaction import redact_sensitive_data


def test_redact_api_key():
    raw = "My OpenAI key is api_key = 'sk-abcdef123456789012345678'"
    assert "[REDACTED_API_KEY]" in redact_sensitive_data(raw)
    assert "sk-abcdef" not in redact_sensitive_data(raw)


def test_redact_db_uri():
    raw = "postgresql://admin:secretPass123@ep-cool.region.neon.tech/synapse"
    assert "[REDACTED_DB_CONNECTION]" in redact_sensitive_data(raw)
    assert "secretPass123" not in redact_sensitive_data(raw)


def test_redact_jwt():
    raw = "Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc123.def456"
    assert "[REDACTED_JWT]" in redact_sensitive_data(raw)
    assert "eyJ" not in redact_sensitive_data(raw)


def test_redact_private_key():
    raw = "-----BEGIN RSA PRIVATE KEY-----MIIEpAIBAAKCAQEA---------------\n-----END RSA PRIVATE KEY-----"
    assert "[REDACTED_PRIVATE_KEY]" in redact_sensitive_data(raw)
    assert "BEGIN RSA PRIVATE KEY" not in redact_sensitive_data(raw)


def test_redact_password():
    raw = "password: 'mySecretPass123'"
    assert "[REDACTED_PASSWORD]" in redact_sensitive_data(raw)
    assert "mySecretPass123" not in redact_sensitive_data(raw)