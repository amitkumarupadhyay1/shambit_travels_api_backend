# Phase 1 Deployment Guide

## 🚀 Quick Deployment Steps

### Pre-Deployment Checklist

```bash
# 1. Verify all checks pass
cd frontend/shambit-frontend
npm run lint
npm run type-check
npm run build

# All should pass with exit code 0
```

### Local Testing

```bash
# 1. Start backend (if not running)
cd backend
python manage.py runserver

# 2. Start frontend dev server
cd frontend/shambit-frontend
npm run dev

# 3. Test these URLs:
# - http://localhost:3000/packages
# - http://localhost:3000/packages/sacred-ayodhya-pilgrimage (or any valid slug)
```

### Staging Deployment

```bash
# 1. Commit changes
git add .
git commit -m "feat: implement Phase 1 MVP - package detail and listing pages"

# 2. Push to staging branch
git push origin staging

# 3. Verify deployment
# Visit: https://your-staging-url.com/packages
```

### Production Deployment

```bash
# 1. Merge to main
git checkout main
git merge staging

# 2. Push to production
git push origin main

# 3. Verify deployment
# Visit: https://shambit.com/packages
```

## 🧪 Testing Checklist

### Functional Testing
- [ ] Homepage loads
- [ ] Click on featured package → lands on detail page
- [ ] Navigate to /packages → listing page loads
- [ ] Search packages → filters correctly
- [ ] Filter by city → shows only that city's packages
- [ ] Click package card → lands on detail page
- [ ] Select experiences → checkboxes work
- [ ] Select hotel tier → radio buttons work
- [ ] Select transport → radio buttons work
- [ ] Price calculator updates → shows correct price
- [ ] Click "Book Now" → shows alert (booking flow not implemented)

### Browser Testing
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

### Device Testing
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

### Performance Testing
- [ ] Lighthouse score > 90
- [ ] Page load < 2s
- [ ] No console errors
- [ ] No memory leaks

## 📊 Monitoring Setup

### Analytics Events to Track

```typescript
// Track page views
analytics.page('Package Detail', { slug: packageSlug });
analytics.page('Packages Listing');

// Track user interactions
analytics.track('Experience Selected', {
  experience_id: exp.id,
  package_slug: packageSlug
});

analytics.track('Price Calculated', {
  total_price: price.total_price,
  num_experiences: selections.experiences.length
});

analytics.track('Book Now Clicked', {
  package_slug: packageSlug,
  total_price: price.total_price
});
```

### Error Monitoring

```typescript
// Setup Sentry (if not already)
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
});
```

## 🔧 Troubleshooting

### Issue: Package detail page shows 404
**Solution:** Verify backend is running and package slug exists in database

### Issue: Price calculator not updating
**Solution:** Check browser console for API errors, verify backend endpoint is accessible

### Issue: Build fails
**Solution:** Run `npm run type-check` to see TypeScript errors

### Issue: Styles not applying
**Solution:** Verify Tailwind CSS is configured correctly, check `globals.css`

## 📞 Support

**Technical Issues:** dev@shambit.com  
**Deployment Issues:** devops@shambit.com  
**Business Questions:** product@shambit.com

---

**Deployment Date:** February 7, 2026  
**Version:** 1.0.0 (Phase 1 MVP)  
**Status:** Ready for Deployment
