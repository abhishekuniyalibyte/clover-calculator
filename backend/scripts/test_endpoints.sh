#!/bin/bash
# Endpoint Testing Script - Manual curl commands
# Run this after starting: python manage.py runserver

BASE_URL="http://localhost:8000/api/v1"

echo "============================================"
echo "Clover Calculator API - Manual Testing"
echo "============================================"
echo ""

# Step 1: Login
echo "1. Testing Authentication..."
read -p "Enter username [abhishekchoudhary]: " USERNAME
USERNAME=${USERNAME:-abhishekchoudhary}
read -sp "Enter password: " PASSWORD
echo ""
PASSWORD=${PASSWORD:-admin}

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/accounts/login/" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed!"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✓ Login successful!"
echo ""

# Headers for authenticated requests
AUTH_HEADER="Authorization: Bearer $TOKEN"

# Step 2: Get analysis ID
echo "2. Getting analysis for testing..."
ANALYSES=$(curl -s -X GET "$BASE_URL/analyses/" \
  -H "$AUTH_HEADER")

echo "$ANALYSES" | grep -q '"results"'
if [ $? -eq 0 ]; then
    ANALYSIS_ID=$(echo $ANALYSES | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    echo "✓ Using analysis ID: $ANALYSIS_ID"
else
    read -p "Enter analysis ID to use for testing: " ANALYSIS_ID
fi
echo ""

# Step 3: Test Device Catalog
echo "3. Testing Device Catalog..."
echo "GET /catalog/devices/"
curl -s -X GET "$BASE_URL/analyses/catalog/devices/" \
  -H "$AUTH_HEADER" | head -c 200
echo "..."
echo ""

# Step 4: Test SaaS Catalog
echo "4. Testing SaaS Catalog..."
echo "GET /catalog/saas/"
curl -s -X GET "$BASE_URL/analyses/catalog/saas/" \
  -H "$AUTH_HEADER" | head -c 200
echo "..."
echo ""

# Step 5: Test Merchant Hardware CRUD
echo "5. Testing Merchant Hardware Endpoints..."

echo "POST /hardware/ (Create)"
HARDWARE=$(curl -s -X POST "$BASE_URL/analyses/hardware/" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"analysis\": $ANALYSIS_ID,
    \"item_type\": \"POS_TERMINAL\",
    \"item_name\": \"Test Square Terminal\",
    \"provider\": \"Square\",
    \"cost_type\": \"MONTHLY_LEASE\",
    \"amount\": \"60.00\",
    \"quantity\": 2
  }")

HARDWARE_ID=$(echo $HARDWARE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ ! -z "$HARDWARE_ID" ]; then
    echo "✓ Created hardware ID: $HARDWARE_ID"

    echo "GET /hardware/ (List)"
    curl -s -X GET "$BASE_URL/analyses/hardware/" \
      -H "$AUTH_HEADER" | head -c 100
    echo "..."

    echo "GET /hardware/$HARDWARE_ID/ (Detail)"
    curl -s -X GET "$BASE_URL/analyses/hardware/$HARDWARE_ID/" \
      -H "$AUTH_HEADER" | head -c 100
    echo "..."

    echo "DELETE /hardware/$HARDWARE_ID/ (Delete)"
    curl -s -X DELETE "$BASE_URL/analyses/hardware/$HARDWARE_ID/" \
      -H "$AUTH_HEADER"
    echo "✓ Deleted"
else
    echo "❌ Failed to create hardware"
fi
echo ""

# Step 6: Test Pricing Model CRUD
echo "6. Testing Pricing Model Endpoints..."

echo "POST /pricing-models/ (Create)"
PRICING=$(curl -s -X POST "$BASE_URL/analyses/pricing-models/" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"analysis\": $ANALYSIS_ID,
    \"model_type\": \"COST_PLUS\",
    \"is_selected\": true,
    \"markup_percent\": \"0.50\",
    \"basis_points\": 10,
    \"per_transaction_fee\": \"0.10\",
    \"monthly_fee\": \"25.00\"
  }")

PRICING_ID=$(echo $PRICING | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ ! -z "$PRICING_ID" ]; then
    echo "✓ Created pricing model ID: $PRICING_ID"

    echo "GET /pricing-models/ (List)"
    curl -s -X GET "$BASE_URL/analyses/pricing-models/" \
      -H "$AUTH_HEADER" | head -c 100
    echo "..."

    echo "DELETE /pricing-models/$PRICING_ID/ (Delete)"
    curl -s -X DELETE "$BASE_URL/analyses/pricing-models/$PRICING_ID/" \
      -H "$AUTH_HEADER"
    echo "✓ Deleted"
else
    echo "❌ Failed to create pricing model"
fi
echo ""

# Step 7: Test One-Time Fee CRUD
echo "7. Testing One-Time Fee Endpoints..."

echo "POST /onetime-fees/ (Create)"
FEE=$(curl -s -X POST "$BASE_URL/analyses/onetime-fees/" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{
    \"analysis\": $ANALYSIS_ID,
    \"fee_type\": \"APPLICATION\",
    \"fee_name\": \"Test Application Fee\",
    \"amount\": \"99.00\",
    \"is_optional\": false
  }")

FEE_ID=$(echo $FEE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ ! -z "$FEE_ID" ]; then
    echo "✓ Created one-time fee ID: $FEE_ID"

    echo "GET /onetime-fees/ (List)"
    curl -s -X GET "$BASE_URL/analyses/onetime-fees/" \
      -H "$AUTH_HEADER" | head -c 100
    echo "..."

    echo "DELETE /onetime-fees/$FEE_ID/ (Delete)"
    curl -s -X DELETE "$BASE_URL/analyses/onetime-fees/$FEE_ID/" \
      -H "$AUTH_HEADER"
    echo "✓ Deleted"
else
    echo "❌ Failed to create one-time fee"
fi
echo ""

echo "============================================"
echo "✓ Testing complete!"
echo "============================================"
echo ""
echo "For more detailed testing, run: python test_endpoints.py"
