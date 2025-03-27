# token_manager

Token manager for handling JWT token storage and revocation.

**Module Path**: `proxmox_nli.core.security.token_manager`

## Classes

### TokenManager

#### __init__()

#### revoke_token(token: str)

Add a token to the revoked tokens list

**Returns**: `None`

#### is_token_revoked(token: str)

Check if a token has been revoked

**Returns**: `bool`

#### clear_revoked_tokens()

Clear all revoked tokens

**Returns**: `None`

