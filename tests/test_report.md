# API Test Report

Generated on: 2026-02-04 15:46:03

| Path | Method | Status | Duration (s) |
|------|--------|--------|--------------|
| /api/cities/city-context/goa-beaches/ | GET | ❌ 404 | 4.52 |
| /api/articles/ | GET | ✅ 200 | 4.40 |
| /api/articles/goa-beaches/ | GET | ❌ 404 | 4.35 |
| /api/packages/packages/ | GET | ✅ 200 | 5.17 |
| /api/packages/packages/goa-beaches/ | GET | ✅ 200 | 5.00 |
| /api/packages/packages/goa-beaches/calculate_price/ | POST | ❌ 400 | 5.32 |
| /api/packages/packages/goa-beaches/price_range/ | GET | ✅ 200 | 6.97 |
| /api/packages/experiences/ | GET | ✅ 200 | 4.46 |
| /api/packages/experiences/1/ | GET | ✅ 200 | 4.29 |
| /api/packages/hotel-tiers/ | GET | ✅ 200 | 4.46 |
| /api/packages/hotel-tiers/1/ | GET | ✅ 200 | 4.17 |
| /api/packages/transport-options/ | GET | ✅ 200 | 4.43 |
| /api/packages/transport-options/1/ | GET | ✅ 200 | 4.18 |
| /api/bookings/ | GET | ✅ 200 | 4.21 |
| /api/bookings/1/ | GET | ❌ 404 | 4.26 |
| /api/notifications/ | GET | ✅ 200 | 4.26 |
| /api/notifications/recent/ | GET | ✅ 200 | 4.11 |
| /api/notifications/stats/ | GET | ✅ 200 | 4.30 |
| /api/notifications/unread/ | GET | ✅ 200 | 4.20 |
| /api/notifications/1/ | GET | ❌ 404 | 4.20 |
| /api/seo/data/ | GET | ✅ 200 | 4.22 |
| /api/seo/data/by_content_type/ | GET | ✅ 200 | 4.19 |
| /api/seo/data/content_types/ | GET | ✅ 200 | 5.32 |
| /api/seo/data/for_object/ | GET | ❌ 400 | 4.07 |
| /api/seo/data/missing_seo/ | GET | ❌ 400 | 3.99 |
| /api/seo/data/stats/ | GET | ✅ 200 | 5.13 |
| /api/seo/data/1/ | GET | ❌ 404 | 4.18 |
| /api/seo/data/1/meta_tags/ | GET | ❌ 404 | 4.19 |
| /api/seo/data/1/structured_data/ | GET | ❌ 404 | 4.15 |
| /api/seo/tools/seo_health_check/ | GET | ✅ 200 | 4.19 |
| /api/media/ | GET | ✅ 200 | 4.14 |
| /api/media/by_content_type/ | GET | ✅ 200 | 4.24 |
| /api/media/content_types/ | GET | ✅ 200 | 5.41 |
| /api/media/for_object/ | GET | ❌ 400 | 3.93 |
| /api/media/gallery/ | GET | ✅ 200 | 4.19 |
| /api/media/orphaned/ | GET | ✅ 200 | 4.19 |
| /api/media/recent/ | GET | ✅ 200 | 4.17 |
| /api/media/stats/ | GET | ✅ 200 | 7.35 |
| /api/media/1/ | GET | ❌ 404 | 4.18 |
| /api/media/1/download/ | GET | ❌ 404 | 4.19 |
| /api/media/1/thumbnail/ | GET | ❌ 404 | 4.79 |
| /api/media/tools/storage_info/ | GET | ❌ 500 | 4.12 |
| /api/pricing/rules/ | GET | ✅ 200 | 4.45 |
| /api/pricing/rules/active_rules/ | GET | ✅ 200 | 4.38 |
| /api/pricing/rules/test_pricing/ | POST | ❌ 400 | 4.21 |
| /api/pricing/rules/1/ | GET | ✅ 200 | 4.18 |

## Summary
- Total Tested: 46
- Success: 30
- Failures/Errors: 16
