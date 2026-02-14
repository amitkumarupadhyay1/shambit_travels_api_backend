# Deployment Checklist - SMS Password Reset

## Backend Changes Summary

✅ Password reset now uses SMS (Fast2SMS) instead of email
✅ Changed from email-based to phone-based authentication
✅ All code changes complete and tested

## Files Modified

1. `backend/apps/users/serializers.py` - Changed email to phone fields
2. `backend/apps/users/auth_views.py` - Updated to use SMS OTP
3. `backend/backend/settings/production.py` - Added Fast2SMS config
4. `backend/backend/settings/base.py` - Added Fast2SMS config

## Railway Deployment Steps

### 1. Verify Environment Variable

In Railway Dashboard → Your Backend Service → Variables:

```bash
FAST2SMS_API_KEY=your-fast2sms-api-key-here
```

**Check:** This should already be set based on your `.env` file.

### 2. Deploy Backend

Option A: **Automatic (Recommended)**
- Push changes to your Git repository
- Railway will auto-deploy

Option B: **Manual**
- Railway Dashboard → Your Service → Deploy → Redeploy

### 3. Wait for Deployment

- Monitor deployment logs in Railway
- Wait for "Build successful" and "Deployment live"
- Usually takes 2-3 minutes

### 4. Test the API

Test forgot password endpoint:

```bash
curl -X POST https://shambit.up.railway.app/api/auth/forgot-password/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210"}'
```

Expected response:
```json
{
  "message": "OTP sent to your phone"
}
```

Check your phone for SMS with OTP.

### 5. Test Reset Password

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

Expected response:
```json
{
  "message": "Password reset successful"
}
```

## Frontend Changes Required

### Update Forgot Password Component

**Before (Email-based):**
```typescript
const handleForgotPassword = async (email: string) => {
  try {
    await axios.post('/api/auth/forgot-password/', { email });
    toast.success('OTP sent to your email');
  } catch (error) {
    toast.error('Failed to send OTP');
  }
};
```

**After (Phone-based):**
```typescript
const handleForgotPassword = async (phone: string) => {
  try {
    await axios.post('/api/auth/forgot-password/', { phone });
    toast.success('OTP sent to your phone');
  } catch (error) {
    toast.error('Failed to send OTP');
  }
};
```

### Update Reset Password Component

**Before:**
```typescript
const handleResetPassword = async (
  email: string,
  otp: string,
  password: string
) => {
  try {
    await axios.post('/api/auth/reset-password/', {
      email,
      otp,
      password,
      password_confirm: password
    });
    toast.success('Password reset successful');
  } catch (error) {
    toast.error('Failed to reset password');
  }
};
```

**After:**
```typescript
const handleResetPassword = async (
  phone: string,
  otp: string,
  password: string
) => {
  try {
    await axios.post('/api/auth/reset-password/', {
      phone,
      otp,
      password,
      password_confirm: password
    });
    toast.success('Password reset successful');
  } catch (error) {
    toast.error('Failed to reset password');
  }
};
```

### Update Form Fields

Change input fields from email to phone:

```tsx
// Before
<input
  type="email"
  name="email"
  placeholder="Enter your email"
  required
/>

// After
<input
  type="tel"
  name="phone"
  placeholder="Enter your phone number"
  pattern="[0-9+]{10,13}"
  required
/>
```

## Testing Checklist

### Backend Testing

- [ ] Deploy backend to Railway
- [ ] Verify FAST2SMS_API_KEY is set in Railway
- [ ] Test `/api/auth/forgot-password/` with curl
- [ ] Receive SMS with OTP
- [ ] Test `/api/auth/reset-password/` with OTP
- [ ] Verify password is changed
- [ ] Check Railway logs for any errors

### Frontend Testing

- [ ] Update forgot password form to use phone
- [ ] Update reset password form to use phone
- [ ] Test forgot password flow end-to-end
- [ ] Verify SMS is received
- [ ] Test reset password with OTP
- [ ] Verify login with new password works
- [ ] Test error cases (invalid phone, wrong OTP, etc.)

## Rollback Plan

If something goes wrong:

### Backend Rollback

1. In Railway Dashboard → Deployments
2. Find previous working deployment
3. Click "Redeploy" on that version

### Frontend Rollback

1. Revert frontend changes
2. Change phone fields back to email
3. Redeploy frontend

## Monitoring

### After Deployment

1. **Railway Logs:** Monitor for errors
   - Railway Dashboard → Your Service → Logs

2. **Fast2SMS Dashboard:** Check SMS delivery
   - https://www.fast2sms.com/dashboard
   - Monitor delivery rate
   - Check remaining credits

3. **User Feedback:** Monitor for user reports
   - SMS not received
   - OTP not working
   - Any other issues

## Common Issues & Solutions

### Issue: "Failed to send SMS"

**Solution:**
- Check Fast2SMS API key in Railway
- Verify Fast2SMS account has credits
- Check Fast2SMS dashboard for failed messages

### Issue: "User with this phone number not found"

**Solution:**
- Ensure user has phone number in profile
- Check phone number format matches database
- Verify user exists in database

### Issue: "Invalid or expired OTP"

**Solution:**
- OTP expires after 5 minutes
- Ensure correct phone number is used
- Request new OTP if expired

## Success Criteria

✅ Backend deployed successfully
✅ SMS OTP received on phone
✅ Password reset works end-to-end
✅ No errors in Railway logs
✅ Fast2SMS dashboard shows successful delivery
✅ Frontend updated and tested

## Next Steps After Deployment

1. Monitor SMS delivery rates for 24 hours
2. Check Fast2SMS credit usage
3. Gather user feedback
4. Consider adding phone number verification during registration
5. Update user documentation/help pages

## Support

If you encounter issues:
- Check `SMS_PASSWORD_RESET.md` for detailed documentation
- Review Railway logs for error messages
- Check Fast2SMS dashboard for delivery status
- Verify environment variables are set correctly
