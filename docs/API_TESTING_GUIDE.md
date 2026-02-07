# API Testing Guide: Experiences Endpoints

## 🎯 Purpose
Verify that all experience-related API endpoints are working correctly before frontend implementation.

---

## 🔧 Prerequisites

1. **Backend Running:**
   ```bash
   cd backend
   python manage.py runserver
   ```

2. **Base URL:**
   - Local: `http://localhost:8000/api`
   - Production: `https://shambit.up.railway.app/api`

3. **Tools:**
   - Browser (for GET requests)
   - Postman/Insomnia (for POST requests)
   - curl (command line)
   - Or use Swagger UI: `http://localhost:8000/api/docs/`

---

## 📋 Test Checklist

### ✅ Test 1: List All Experiences

**Endpoint:** `GET /api/packages/experiences/`

**Expected Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "City Walking Tour",
      "description": "Explore the city with a local guide...",
      "base_price": "2500.00",
      "created_at": "2026-01-15T10:30:00Z"
    },
    ...
  ]
}
```

**Test Commands:**

**Browser:**
```
http://localhost:8000/api/packages/experiences/
```

**curl:**
```bash
curl -X GET "http://localhost:8000/api/packages/experiences/" \
  -H "Accept: application/json"
```

**Verification:**
- [ ] Status code: 200 OK
- [ ] Returns paginated response
- [ ] Contains array of experiences
- [ ] Each experience has: id, name, description, base_price, created_at
- [ ] Prices are in decimal format

---

### ✅ Test 2: Get Single Experience

**Endpoint:** `GET /api/packages/experiences/{id}/`

**Expected Response:**
```json
{
  "id": 1,
  "name": "City Walking Tour",
  "description": "Explore the city with a local guide through historic streets...",
  "base_price": "2500.00",
  "created_at": "2026-01-15T10:30:00Z"
}
```

**Test Commands:**

**Browser:**
```
http://localhost:8000/api/packages/experiences/1/
```

**curl:**
```bash
curl -X GET "http://localhost:8000/api/packages/experiences/1/" \
  -H "Accept: application/json"
```

**Verification:**
- [ ] Status code: 200 OK
- [ ] Returns single experience object
- [ ] All fields present and correct
- [ ] Invalid ID returns 404

---

### ✅ Test 3: List All Packages (with Experiences)

**Endpoint:** `GET /api/packages/packages/`

**Expected Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Sacred Ayodhya Pilgrimage",
      "slug": "sacred-ayodhya-pilgrimage",
      "description": "A comprehensive 3-day spiritual journey...",
      "city_name": "Ayodhya",
      "experiences": [
        {
          "id": 1,
          "name": "Ram Mandir Morning Darshan",
          "description": "...",
          "base_price": "1500.00",
          "created_at": "2026-01-15T10:30:00Z"
        },
        ...
      ],
      "hotel_tiers": [...],
      "transport_options": [...],
      "is_active": true,
      "created_at": "2026-01-20T14:00:00Z"
    },
    ...
  ]
}
```

**Test Commands:**

**Browser:**
```
http://localhost:8000/api/packages/packages/
```

**curl:**
```bash
curl -X GET "http://localhost:8000/api/packages/packages/" \
  -H "Accept: application/json"
```

**Verification:**
- [ ] Status code: 200 OK
- [ ] Returns paginated response
- [ ] Each package includes nested experiences array
- [ ] Experiences have all required fields
- [ ] Hotel tiers and transport options also included

---

### ✅ Test 4: Get Package by Slug

**Endpoint:** `GET /api/packages/packages/{slug}/`

**Expected Response:**
```json
{
  "id": 1,
  "name": "Sacred Ayodhya Pilgrimage",
  "slug": "sacred-ayodhya-pilgrimage",
  "description": "A comprehensive 3-day spiritual journey through Ayodhya...",
  "city_name": "Ayodhya",
  "experiences": [
    {
      "id": 1,
      "name": "Ram Mandir Morning Darshan",
      "description": "Experience divine morning aarti...",
      "base_price": "1500.00",
      "created_at": "2026-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "name": "Sarayu River Boat Ride",
      "description": "Peaceful boat ride on sacred river...",
      "base_price": "800.00",
      "created_at": "2026-01-15T10:35:00Z"
    }
  ],
  "hotel_tiers": [
    {
      "id": 1,
      "name": "Budget",
      "description": "Clean and comfortable budget hotels",
      "price_multiplier": "1.50"
    },
    {
      "id": 2,
      "name": "Standard",
      "description": "3-star hotels with modern amenities",
      "price_multiplier": "2.50"
    }
  ],
  "transport_options": [
    {
      "id": 1,
      "name": "AC Bus",
      "description": "Comfortable AC bus transport",
      "base_price": "500.00"
    },
    {
      "id": 2,
      "name": "Train",
      "description": "AC train travel",
      "base_price": "800.00"
    }
  ],
  "is_active": true,
  "created_at": "2026-01-20T14:00:00Z"
}
```

**Test Commands:**

**Browser:**
```
http://localhost:8000/api/packages/packages/sacred-ayodhya-pilgrimage/
```

**curl:**
```bash
curl -X GET "http://localhost:8000/api/packages/packages/sacred-ayodhya-pilgrimage/" \
  -H "Accept: application/json"
```

**Verification:**
- [ ] Status code: 200 OK
- [ ] Returns complete package details
- [ ] All experiences listed with full details
- [ ] Hotel tiers with multipliers
- [ ] Transport options with prices
- [ ] Invalid slug returns 404

---

### ✅ Test 5: Filter Packages by City

**Endpoint:** `GET /api/packages/packages/?city={city_id}`

**Expected Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Sacred Ayodhya Pilgrimage",
      "city_name": "Ayodhya",
      "experiences": [...],
      ...
    },
    {
      "id": 2,
      "name": "Ayodhya Heritage Tour",
      "city_name": "Ayodhya",
      "experiences": [...],
      ...
    }
  ]
}
```

**Test Commands:**

**Browser:**
```
http://localhost:8000/api/packages/packages/?city=4
```

**curl:**
```bash
curl -X GET "http://localhost:8000/api/packages/packages/?city=4" \
  -H "Accept: application/json"
```

**Verification:**
- [ ] Status code: 200 OK
- [ ] Returns only packages for specified city
- [ ] All packages have matching city_name
- [ ] Empty result if no packages for city

---

### ✅ Test 6: Get Price Range for Package

**Endpoint:** `GET /api/packages/packages/{slug}/price_range/`

**Expected Response:**
```json
{
  "package": "Sacred Ayodhya Pilgrimage",
  "price_range": {
    "min_price": "5100.00",
    "max_price": "15750.00",
    "currency": "INR"
  },
  "note": "Prices are estimates and may vary based on selected components and active promotions"
}
```

**Test Commands:**

**Browser:**
```
http://localhost:8000/api/packages/packages/sacred-ayodhya-pilgrimage/price_range/
```

**curl:**
```bash
curl -X GET "http://localhost:8000/api/packages/packages/sacred-ayodhya-pilgrimage/price_range/" \
  -H "Accept: application/json"
```

**Verification:**
- [ ] Status code: 200 OK
- [ ] Returns min and max prices
- [ ] Prices are in decimal format
- [ ] Currency is INR
- [ ] Min price < Max price

---

### ✅ Test 7: Calculate Package Price (POST)

**Endpoint:** `POST /api/packages/packages/{slug}/calculate_price/`

**Request Body:**
```json
{
  "experience_ids": [1, 2],
  "hotel_tier_id": 1,
  "transport_option_id": 1
}
```

**Expected Response:**
```json
{
  "total_price": "5100.00",
  "currency": "INR",
  "breakdown": {
    "experiences": [
      {
        "id": 1,
        "name": "Ram Mandir Morning Darshan",
        "price": "1500.00"
      },
      {
        "id": 2,
        "name": "Sarayu River Boat Ride",
        "price": "800.00"
      }
    ],
    "hotel_tier": {
      "id": 1,
      "name": "Budget",
      "price_multiplier": "1.50"
    },
    "transport": {
      "id": 1,
      "name": "AC Bus",
      "price": "500.00"
    }
  },
  "pricing_note": "This is an estimate. Final price calculated at checkout."
}
```

**Test Commands:**

**curl:**
```bash
curl -X POST "http://localhost:8000/api/packages/packages/sacred-ayodhya-pilgrimage/calculate_price/" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "experience_ids": [1, 2],
    "hotel_tier_id": 1,
    "transport_option_id": 1
  }'
```

**Postman/Insomnia:**
1. Method: POST
2. URL: `http://localhost:8000/api/packages/packages/sacred-ayodhya-pilgrimage/calculate_price/`
3. Headers:
   - Content-Type: application/json
   - Accept: application/json
4. Body (raw JSON):
   ```json
   {
     "experience_ids": [1, 2],
     "hotel_tier_id": 1,
     "transport_option_id": 1
   }
   ```

**Verification:**
- [ ] Status code: 200 OK
- [ ] Returns total_price
- [ ] Breakdown includes all selected components
- [ ] Prices match expected calculation
- [ ] Invalid IDs return 400 Bad Request

**Manual Price Verification:**
```
Experience 1: ₹1,500
Experience 2: ₹800
Transport: ₹500
Subtotal: ₹2,800

Hotel Multiplier: 1.5x
After Hotel: ₹2,800 × 1.5 = ₹4,200

(If no pricing rules)
Final Total: ₹4,200
```

---

### ✅ Test 8: Calculate Price with Multiple Experiences

**Request Body:**
```json
{
  "experience_ids": [1, 2, 3],
  "hotel_tier_id": 2,
  "transport_option_id": 2
}
```

**Expected Calculation:**
```
Experience 1: ₹1,500
Experience 2: ₹800
Experience 3: ₹600
Transport: ₹800
Subtotal: ₹3,700

Hotel Multiplier: 2.5x
After Hotel: ₹3,700 × 2.5 = ₹9,250

Final Total: ₹9,250
```

**Verification:**
- [ ] Handles multiple experiences correctly
- [ ] Applies correct hotel multiplier
- [ ] Includes all components in breakdown

---

### ✅ Test 9: Error Handling - Invalid Experience ID

**Request Body:**
```json
{
  "experience_ids": [999],
  "hotel_tier_id": 1,
  "transport_option_id": 1
}
```

**Expected Response:**
```json
{
  "error": "One or more experiences not found"
}
```

**Verification:**
- [ ] Status code: 400 Bad Request
- [ ] Returns clear error message
- [ ] Does not crash or return 500

---

### ✅ Test 10: Error Handling - Missing Required Fields

**Request Body:**
```json
{
  "experience_ids": [1, 2]
}
```

**Expected Response:**
```json
{
  "error": "hotel_tier_id and transport_option_id are required"
}
```

**Verification:**
- [ ] Status code: 400 Bad Request
- [ ] Returns validation error
- [ ] Specifies which fields are missing

---

## 🔍 Advanced Testing

### Test 11: Pagination

**Test Large Result Sets:**
```bash
curl -X GET "http://localhost:8000/api/packages/experiences/?page=1" \
  -H "Accept: application/json"
```

**Verification:**
- [ ] Returns first page of results
- [ ] Includes `next` and `previous` links
- [ ] `count` shows total number of experiences

### Test 12: Performance

**Test Response Time:**
```bash
time curl -X GET "http://localhost:8000/api/packages/packages/" \
  -H "Accept: application/json"
```

**Verification:**
- [ ] Response time < 500ms
- [ ] No N+1 query issues
- [ ] Proper use of select_related/prefetch_related

### Test 13: Concurrent Requests

**Test Multiple Simultaneous Requests:**
```bash
for i in {1..10}; do
  curl -X GET "http://localhost:8000/api/packages/experiences/" &
done
wait
```

**Verification:**
- [ ] All requests succeed
- [ ] No race conditions
- [ ] Consistent responses

---

## 📊 Test Results Template

```markdown
## API Test Results - [Date]

### Environment
- Backend URL: [URL]
- Database: [PostgreSQL/SQLite]
- Test Tool: [Browser/curl/Postman]

### Test Summary
| Test | Endpoint | Status | Response Time | Notes |
|------|----------|--------|---------------|-------|
| 1 | GET /experiences/ | ✅ Pass | 150ms | - |
| 2 | GET /experiences/{id}/ | ✅ Pass | 80ms | - |
| 3 | GET /packages/ | ✅ Pass | 200ms | - |
| 4 | GET /packages/{slug}/ | ✅ Pass | 180ms | - |
| 5 | GET /packages/?city=4 | ✅ Pass | 190ms | - |
| 6 | GET /price_range/ | ✅ Pass | 120ms | - |
| 7 | POST /calculate_price/ | ✅ Pass | 250ms | - |
| 8 | POST /calculate_price/ (multi) | ✅ Pass | 280ms | - |
| 9 | Error: Invalid ID | ✅ Pass | 100ms | Correct 400 |
| 10 | Error: Missing fields | ✅ Pass | 90ms | Correct 400 |

### Issues Found
- None

### Recommendations
- All endpoints working correctly
- Ready for frontend integration
```

---

## 🚀 Quick Test Script

Save this as `test_experiences_api.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api"

echo "🧪 Testing Experiences API..."
echo ""

echo "Test 1: List Experiences"
curl -s -X GET "$BASE_URL/packages/experiences/" | jq '.count'
echo ""

echo "Test 2: Get Single Experience"
curl -s -X GET "$BASE_URL/packages/experiences/1/" | jq '.name'
echo ""

echo "Test 3: List Packages"
curl -s -X GET "$BASE_URL/packages/packages/" | jq '.count'
echo ""

echo "Test 4: Get Package by Slug"
curl -s -X GET "$BASE_URL/packages/packages/sacred-ayodhya-pilgrimage/" | jq '.name'
echo ""

echo "Test 5: Filter by City"
curl -s -X GET "$BASE_URL/packages/packages/?city=4" | jq '.count'
echo ""

echo "Test 6: Price Range"
curl -s -X GET "$BASE_URL/packages/packages/sacred-ayodhya-pilgrimage/price_range/" | jq '.price_range'
echo ""

echo "Test 7: Calculate Price"
curl -s -X POST "$BASE_URL/packages/packages/sacred-ayodhya-pilgrimage/calculate_price/" \
  -H "Content-Type: application/json" \
  -d '{"experience_ids":[1,2],"hotel_tier_id":1,"transport_option_id":1}' | jq '.total_price'
echo ""

echo "✅ All tests complete!"
```

**Run:**
```bash
chmod +x test_experiences_api.sh
./test_experiences_api.sh
```

---

## 📝 Swagger UI Testing

**Easiest Method:** Use built-in Swagger UI

1. **Open Swagger:**
   ```
   http://localhost:8000/api/docs/
   ```

2. **Navigate to "Packages" section**

3. **Test Each Endpoint:**
   - Click endpoint
   - Click "Try it out"
   - Fill in parameters
   - Click "Execute"
   - View response

**Advantages:**
- Visual interface
- Auto-generated examples
- Schema validation
- No command line needed

---

## ✅ Final Checklist

Before declaring API ready for frontend:

- [ ] All GET endpoints return 200 OK
- [ ] POST endpoint accepts valid data
- [ ] Error handling works correctly
- [ ] Response times < 500ms
- [ ] Pagination works
- [ ] Filtering works
- [ ] Nested data (experiences in packages) loads correctly
- [ ] Price calculations are accurate
- [ ] Documentation is accurate
- [ ] No console errors in backend logs

---

## 🎯 Next Steps

Once all tests pass:

1. ✅ Document test results
2. ✅ Share with frontend team
3. ✅ Provide API documentation link
4. ✅ Begin frontend implementation
5. ✅ Setup integration testing

---

**Questions?** Contact: api-support@shambit.com

**Documentation:** `/api/docs/` or `/api/redoc/`

---

**Document Version:** 1.0  
**Last Updated:** February 7, 2026  
**Status:** Ready for Testing
