# Quick Start - SMS Password Reset

## What Changed?

Password reset now uses **SMS (Fast2SMS)** instead of email.

## Why?

✅ Instant delivery (SMS arrives in seconds)
✅ Better for Indian users
✅ Confirms phone numbers (critical for bookings)
✅ No email setup needed
✅ Works immediately on Railway

## Backend - Ready to Deploy

All backend changes are complete. Just deploy to Railway.

### What Was Changed:

1. Forgot password accepts `phone` instead of `email`
2. Reset password accepts `phone` instead of `email`
3. Uses Fast2SMS API for sending OTP
4. Fast2SMS API key already configured in your `.env`

### Deploy:

```bash
# Push to Git (Railway auto-deploys)
git add .
git commit -m "Switch password reset to SMS"
git push
```

## Frontend - Needs Update

Update your forgot/reset password forms:

### Change 1: Forgot Password Form

```typescript
// OLD - Remove this
const forgotPassword = async (email: string) => {
  await axios.post('/api/auth/forgot-password/', { email });
};

// NEW - Use this
const forgotPassword = async (phone: string) => {
  await axios.post('/api/auth/forgot-password/', { phone });
};
```

### Change 2: Reset Password Form

```typescript
// OLD - Remove this
const resetPassword = async (email: string, otp: string, password: string) => {
  await axios.post('/api/auth/reset-password/', {
    email, otp, password, password_confirm: password
  });
};

// NEW - Use this
const resetPassword = async (phone: string, otp: string, password: string) => {
  await axios.post('/api/auth/reset-password/', {
    phone, otp, password, password_confirm: password
  });
};
```

### Change 3: Form Input

```tsx
<!-- OLD - Remove this -->
<input type="email" name="email" placeholder="Enter your email" />

<!-- NEW - Use this -->
<input type="tel" name="phone" placeholder="Enter your phone number" />
```

## Test It

### 1. Test Backend (After Deploy)

```bash
curl -X POST https://shambit.up.railway.app/api/auth/forgot-password/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210"}'
```

You should receive SMS with OTP.

### 2. Test Frontend

1. Go to forgot password page
2. Enter phone number
3. Click submit
4. Check phone for SMS
5. Enter OTP and new password
6. Submit
7. Login with new password

## That's It!

Backend is ready. Update frontend forms from email to phone. Deploy. Test.

## Need Help?

- Detailed docs: `SMS_PASSWORD_RESET.md`
- Deployment guide: `DEPLOYMENT_CHECKLIST.md`
- Check Railway logs if SMS not received
- Verify Fast2SMS API key is set in Railway variables
