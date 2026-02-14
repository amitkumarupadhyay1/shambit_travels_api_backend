# SMS-Based Password Reset Implementation

## Overview

Password reset now uses SMS OTP via Fast2SMS instead of email. This is better for Indian users and confirms phone numbers which are critical for booking confirmations.

## Changes Made

### 1. Updated Serializers (`backend/apps/users/serializers.py`)

**ForgotPasswordSerializer:**
- Changed from `email` field to `phone` field
- Now accepts phone number instead of email

**ResetPasswordSerializer:**
- Changed from `email` field to `phone` field
- Validates OTP against phone number

### 2. Updated Views (`backend/apps/users/auth_views.py`)

**ForgotPasswordView:**
- Accepts phone number instead of email
- Uses `OTPService.send_otp()` (Fast2SMS) instead of `EmailService`
- Looks up user by phone number
- Returns "OTP sent to your phone" message

**ResetPasswordView:**
- Accepts phone number instead of email
- Verifies OTP against phone number
- Resets password for user with matching phone

## API Endpoints

### 1. Request Password Reset

**Endpoint:** `POST /api/auth/forgot-password/`

**Request Body:**
```json
{
  "phone": "+919876543210"
}
```

**Success Response (200):**
```json
{
  "message": "OTP sent to your phone"
}
```

**Error Responses:**
- `404`: User with this phone number not found
- `500`: Failed to send SMS

### 2. Reset Password with OTP

**Endpoint:** `POST /api/auth/reset-password/`

**Request Body:**
```json
{
  "phone": "+919876543210",
  "otp": "123456",
  "password": "newpassword123",
  "password_confirm": "newpassword123"
}
```

**Success Response (200):**
```json
{
  "message": "Password reset successful"
}
```

**Error Responses:**
- `400`: Invalid or expired OTP / Passwords don't match
- `404`: User with this phone number not found

## Fast2SMS Configuration

### Environment Variables Required

In Railway, ensure these variables are set:

```bash
FAST2SMS_API_KEY=your-fast2sms-api-key-here
```

Your current `.env` already has this configured.

### Fast2SMS API Details

- **Service:** Fast2SMS (https://www.fast2sms.com/)
- **Route:** OTP route (optimized for OTP delivery)
- **Timeout:** 5 seconds
- **OTP Validity:** 5 minutes (300 seconds)

## Benefits of SMS-Based Reset

1. **Instant Delivery:** SMS arrives within seconds
2. **Phone Verification:** Confirms user's phone number is valid and accessible
3. **Better for India:** More reliable than email for Indian users
4. **No Email Setup:** Works immediately without email service configuration
5. **Critical for Bookings:** Phone numbers are essential for booking confirmations

## Frontend Integration

### Update Forgot Password Form

Change the form to accept phone number instead of email:

```typescript
// Before (Email)
const forgotPassword = async (email: string) => {
  await axios.post('/api/auth/forgot-password/', { email });
};

// After (Phone)
const forgotPassword = async (phone: string) => {
  await axios.post('/api/auth/forgot-password/', { phone });
};
```

### Update Reset Password Form

```typescript
// Before (Email)
const resetPassword = async (email: string, otp: string, password: string) => {
  await axios.post('/api/auth/reset-password/', {
    email,
    otp,
    password,
    password_confirm: password
  });
};

// After (Phone)
const resetPassword = async (phone: string, otp: string, password: string) => {
  await axios.post('/api/auth/reset-password/', {
    phone,
    otp,
    password,
    password_confirm: password
  });
};
```

## Testing

### 1. Test Forgot Password

```bash
curl -X POST https://shambit.up.railway.app/api/auth/forgot-password/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210"}'
```

Expected: SMS with 6-digit OTP sent to phone

### 2. Test Reset Password

```bash
curl -X POST https://shambit.up.railway.app/api/auth/reset-password/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "otp": "123456",
    "password": "newpassword123",
    "password_confirm": "newpassword123"
  }'
```

Expected: Password reset successful

## Phone Number Format

Fast2SMS accepts Indian phone numbers in these formats:
- `9876543210` (10 digits)
- `+919876543210` (with country code)
- `919876543210` (without + symbol)

The backend accepts any format, but ensure consistency in your frontend.

## OTP Security

- **Validity:** 5 minutes (300 seconds)
- **Storage:** Redis/Cache (automatically expires)
- **One-time use:** OTP is deleted after successful verification
- **Purpose-specific:** OTPs for login and password reset are separate

## Troubleshooting

### "Failed to send SMS"

1. Check Fast2SMS API key is set in Railway environment variables
2. Verify Fast2SMS account has sufficient credits
3. Check Railway logs for detailed error message
4. Ensure phone number is in valid format

### "User with this phone number not found"

- User must have a phone number in their profile
- Phone number must match exactly (including country code format)
- Ensure user registered with phone number

### "Invalid or expired OTP"

- OTP expires after 5 minutes
- OTP can only be used once
- Ensure correct phone number is used
- Check for typos in OTP

## Migration Notes

### Existing Users

Users who registered with email only (no phone) cannot use password reset until they add a phone number to their profile. Consider:

1. Adding a "Update Phone Number" feature in user profile
2. Requiring phone number during registration
3. Sending notification to users without phone numbers

### Database

No migration needed - `phone` field already exists in User model.

## Next Steps

1. **Update Frontend:** Change forgot/reset password forms to use phone instead of email
2. **Test Thoroughly:** Test with real phone numbers
3. **Monitor Fast2SMS:** Check delivery rates and credits in Fast2SMS dashboard
4. **User Communication:** Inform users about the change (if already in production)

## Fast2SMS Dashboard

Monitor SMS delivery at: https://www.fast2sms.com/dashboard

- Check delivery status
- Monitor remaining credits
- View failed messages
- Track usage statistics
