#!/bin/bash
# JWT Smoke Test Script
# Copy-paste from assistant's recommendations

echo "🧪 JWT SYSTEM SMOKE TEST"
echo "========================"

# Configuration
BASE_URL="http://localhost:8000"

echo "Prerequisites: Ensure Django server is running on port 8000"
echo "Usage: Replace <user> and <pass> with actual credentials"
echo ""

echo "# 1) Obtain tokens"
echo "curl -s -X POST $BASE_URL/api/token/ \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\":\"<user>\",\"password\":\"<pass>\"}' | tee /tmp/jwt.json"
echo ""

echo "# Extract tokens (requires jq)"
echo "ACCESS=\$(jq -r .access /tmp/jwt.json)"
echo "REFRESH=\$(jq -r .refresh /tmp/jwt.json)"
echo ""

echo "# 2) Hit protected endpoint"
echo "curl -i $BASE_URL/api/test-auth/ -H \"Authorization: Bearer \$ACCESS\""
echo ""

echo "# 3) Refresh token (should be throttled)"
echo "curl -i -X POST $BASE_URL/api/token/refresh/ \\"
echo "  -H 'Content-Type: application/json' -d \"{\\\"refresh\\\":\\\"\$REFRESH\\\"}\""
echo ""

echo "# 4) Revoke all tokens"  
echo "curl -i -X POST $BASE_URL/api/token/revoke-all/ \\"
echo "  -H \"Authorization: Bearer \$ACCESS\""
echo ""

echo "# 5) Test revoke single token (accepts both 'refresh' and 'refresh_token')"
echo "curl -i -X POST $BASE_URL/api/token/revoke/ \\"
echo "  -H \"Authorization: Bearer \$ACCESS\" \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d \"{\\\"refresh_token\\\":\\\"\$REFRESH\\\"}\""

echo ""
echo "Expected Results:"
echo "- Step 1: Returns access and refresh tokens"
echo "- Step 2: Returns user info (proves JWT works)"
echo "- Step 3: Should apply token_refresh rate limiting"
echo "- Step 4: Revokes all tokens (count returned)"
echo "- Step 5: Works with both 'refresh' and 'refresh_token' fields"
