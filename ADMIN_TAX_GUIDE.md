# Admin Guide: Managing Taxes & Pricing Rules

**For:** ShamBit Platform Administrators  
**Purpose:** Easy tax management when government changes tax rates  
**Last Updated:** February 17, 2026

---

## 🎯 Quick Start

### What You Need to Know

Your platform uses a **flexible pricing rules system** that allows you to:
- ✅ Change GST rate when government updates it
- ✅ Add/remove service charges
- ✅ Create promotional discounts
- ✅ Apply rules to specific packages or all packages
- ✅ Schedule rules for future activation
- ✅ All changes apply immediately - no code deployment needed!

---

## 📋 Table of Contents

1. [Accessing the Admin Panel](#accessing-the-admin-panel)
2. [Understanding Pricing Rules](#understanding-pricing-rules)
3. [Changing GST Rate](#changing-gst-rate)
4. [Adding New Taxes](#adding-new-taxes)
5. [Creating Discounts](#creating-discounts)
6. [Bulk Operations](#bulk-operations)
7. [Troubleshooting](#troubleshooting)

---

## 🔐 Accessing the Admin Panel

### Step 1: Login to Django Admin

1. Open your browser
2. Navigate to: `https://your-domain.com/admin/`
3. Login with your admin credentials

### Step 2: Navigate to Pricing Rules

1. In the left sidebar, find **"Pricing Engine"**
2. Click on **"Pricing Rules"**
3. You'll see a list of all pricing rules

---

## 📚 Understanding Pricing Rules

### Rule Types

**MARKUP** (Orange badge with +)
- Adds to the price
- Used for: GST, service charges, platform fees
- Example: GST (18%) adds 18% to subtotal

**DISCOUNT** (Green badge with -)
- Subtracts from the price
- Used for: Promotions, seasonal offers, early bird discounts
- Example: Summer Sale (10%) reduces price by 10%

### Value Types

**Percentage** (%)
- Calculated as percentage of current price
- Example: 18% GST on ₹10,000 = ₹1,800

**Fixed Amount** (₹)
- Fixed rupee amount
- Example: ₹500 service charge

### Status Badges

- **✓ Active** (Green) - Currently applying to bookings
- **⏰ Scheduled** (Yellow) - Will activate in future
- **⏹ Expired** (Gray) - Past the end date
- **✗ Inactive** (Red) - Manually disabled

---

## 💰 Changing GST Rate

### Scenario: Government Changes GST from 18% to 20%

**Step-by-Step:**

1. **Go to Admin Panel**
   - Navigate to `/admin/pricing_engine/pricingrule/`

2. **Find GST Rule**
   - Look for "GST (18%)" in the list
   - Click on it to edit

3. **Update the Value**
   - Change "Value" from `18.00` to `20.00`
   - Update "Name" to "GST (20%)" (optional but recommended)

4. **Save**
   - Click "Save" button at the bottom
   - ✅ Done! New rate applies immediately to all new bookings

### Important Notes

- ✅ Existing bookings are NOT affected (they keep their original price)
- ✅ New price calculations use the updated rate immediately
- ✅ No server restart needed
- ✅ No code deployment needed
- ⚠️ Make sure "Is Active" checkbox is checked

---

## ➕ Adding New Taxes

### Scenario: Government Introduces New "Tourism Tax" of 5%

**Step-by-Step:**

1. **Go to Pricing Rules**
   - Navigate to `/admin/pricing_engine/pricingrule/`

2. **Click "Add Pricing Rule"**
   - Top right corner

3. **Fill in Details**
   ```
   Name: Tourism Tax (5%)
   Rule Type: Markup
   Value: 5.00
   Is Percentage: ✓ (checked)
   Target Package: (leave empty for all packages)
   Is Active: ✓ (checked)
   Active From: (select current date/time)
   Active To: (leave empty for indefinite)
   ```

4. **Save**
   - Click "Save" button
   - ✅ New tax applies immediately!

### Adding Fixed Amount Tax

Example: ₹200 Environmental Fee

```
Name: Environmental Fee
Rule Type: Markup
Value: 200.00
Is Percentage: ☐ (unchecked)
Target Package: (leave empty)
Is Active: ✓ (checked)
Active From: (current date/time)
Active To: (empty)
```

---

## 🎁 Creating Discounts

### Scenario: 10% Summer Sale Discount

**Step-by-Step:**

1. **Add New Pricing Rule**

2. **Fill in Details**
   ```
   Name: Summer Sale (10% Off)
   Rule Type: Discount  ← Important!
   Value: 10.00
   Is Percentage: ✓ (checked)
   Target Package: (empty for all, or select specific package)
   Is Active: ✓ (checked)
   Active From: 2026-06-01 00:00:00
   Active To: 2026-08-31 23:59:59
   ```

3. **Save**
   - Discount will automatically activate on June 1st
   - And automatically deactivate on September 1st

### Early Bird Discount Example

```
Name: Early Bird - Book 30 Days Advance (15% Off)
Rule Type: Discount
Value: 15.00
Is Percentage: ✓
Target Package: (empty)
Is Active: ✓
Active From: (current date)
Active To: (empty)
```

---

## 🔧 Bulk Operations

### Activating Multiple Rules

1. **Select Rules**
   - Check the boxes next to rules you want to activate

2. **Choose Action**
   - From the "Action" dropdown at the top
   - Select "✓ Activate selected rules"

3. **Click "Go"**
   - All selected rules become active

### Deactivating Multiple Rules

Same process, but select "✗ Deactivate selected rules"

### Duplicating Rules

Useful for creating similar rules:

1. Select the rule to duplicate
2. Choose "📋 Duplicate selected rules"
3. Click "Go"
4. Edit the duplicated rule (it starts as inactive)

---

## 🎯 Common Scenarios

### Scenario 1: Temporary Tax Holiday

**Goal:** Remove GST for a promotional period

**Solution:**
1. Find "GST (18%)" rule
2. Uncheck "Is Active"
3. Save
4. (Remember to re-activate it later!)

**Better Solution:**
1. Set "Active To" date for when tax holiday ends
2. System will automatically reactivate after that date

### Scenario 2: Package-Specific Discount

**Goal:** 20% off only on "Varanasi Spiritual Journey"

**Solution:**
1. Create new discount rule
2. In "Target Package", select "Varanasi Spiritual Journey"
3. Set value to 20.00
4. Save

### Scenario 3: Seasonal Pricing

**Goal:** Higher prices during peak season

**Solution:**
1. Create markup rule: "Peak Season Surcharge (25%)"
2. Set "Active From": December 15, 2026
3. Set "Active To": January 15, 2027
4. System automatically applies during that period

---

## 📊 How Pricing Works

### Calculation Order

```
1. Base Experience Prices
   Example: ₹2,500 + ₹1,500 = ₹4,000

2. + Transport
   Example: ₹4,000 + ₹3,000 = ₹7,000

3. × Hotel Tier Multiplier
   Example: ₹7,000 × 2.5 = ₹17,500

4. + Markups (Taxes, Fees)
   Example: ₹17,500 + 18% GST (₹3,150) + ₹500 = ₹21,150

5. - Discounts
   Example: ₹21,150 - 10% discount (₹2,115) = ₹19,035

6. = Final Total
   Example: ₹19,035
```

### What Customers See

On the frontend, customers see:

```
Selected Experiences
  + Gateway of India Tour: ₹2,500
  + Marine Drive Walk: ₹1,500

4-Star Hotels: ×2.5
AC Cab: ₹3,000

Subtotal: ₹17,500

Taxes & Charges
  + GST (18%): ₹3,150
  + Service Charge: ₹500

Total Payable: ₹21,150

[Badge] Price is per person
[Badge] All taxes included • No hidden charges
```

---

## ⚠️ Important Rules

### DO's ✅

- ✅ Test changes on a test package first
- ✅ Update rule names when changing values (e.g., "GST (18%)" → "GST (20%)")
- ✅ Use "Active From" and "Active To" for scheduled changes
- ✅ Keep inactive rules for historical reference
- ✅ Document why you made changes (in admin notes)

### DON'Ts ❌

- ❌ Don't delete rules - deactivate them instead
- ❌ Don't create duplicate active rules for same tax
- ❌ Don't forget to check "Is Active" when creating new rules
- ❌ Don't set "Active From" in the past if you want immediate effect
- ❌ Don't modify rules during peak booking hours (if possible)

---

## 🔍 Troubleshooting

### Problem: New tax rate not showing on frontend

**Solution:**
1. Check if rule "Is Active" is checked
2. Check if "Active From" date is in the past
3. Check if "Active To" date hasn't passed
4. Clear browser cache and refresh
5. Check if rule applies to the package (Target Package field)

### Problem: Prices seem wrong

**Solution:**
1. Check if multiple rules are active for same thing
2. Verify rule type (MARKUP vs DISCOUNT)
3. Check if percentage vs fixed amount is correct
4. Look at "Applied Rules" in price breakdown

### Problem: Can't edit a rule

**Solution:**
1. Make sure you're logged in as admin
2. Check your user permissions
3. Try logging out and back in

### Problem: Rule not applying to specific package

**Solution:**
1. Check "Target Package" field
2. If it's set to a specific package, it won't apply to others
3. Leave empty to apply to ALL packages

---

## 📞 Getting Help

### Admin Panel Help

- Click the "?" icon next to any field for help
- Hover over field labels for tooltips

### Technical Support

If you need help:
1. Note down the rule name and what you're trying to do
2. Take a screenshot of the admin page
3. Contact your technical team

### Emergency: Need to Disable All Taxes

**Quick Fix:**
1. Go to Pricing Rules
2. Select all tax rules (GST, Service Charge, etc.)
3. Action → "✗ Deactivate selected rules"
4. Click "Go"

---

## 📝 Best Practices

### Naming Conventions

Good names:
- ✅ "GST (18%)"
- ✅ "Service Charge - Platform Fee"
- ✅ "Summer Sale 2026 (10% Off)"
- ✅ "Early Bird Discount - 30 Days Advance"

Bad names:
- ❌ "Tax"
- ❌ "Discount"
- ❌ "Rule 1"

### Documentation

When creating/modifying rules, document:
- Why you created it
- When it should end (if applicable)
- Who requested it
- Any special conditions

### Testing

Before activating a new rule:
1. Create it as inactive first
2. Test on a test package
3. Verify price calculation
4. Then activate for all packages

---

## 🎓 Training Checklist

New admins should know how to:
- [ ] Access the admin panel
- [ ] Find pricing rules
- [ ] Change GST rate
- [ ] Add a new tax
- [ ] Create a discount
- [ ] Activate/deactivate rules
- [ ] Use bulk operations
- [ ] Troubleshoot common issues

---

## 📅 Maintenance Schedule

### Monthly
- Review active rules
- Check for expired rules
- Clean up inactive test rules

### Quarterly
- Review pricing strategy
- Analyze discount effectiveness
- Update documentation

### When Government Changes Tax Rates
- Update GST rule immediately
- Test on staging first (if available)
- Notify team of changes
- Update customer-facing documentation

---

## 🚀 Quick Reference Card

### Change GST Rate
```
Admin → Pricing Rules → GST (18%) → Edit
Change Value → Save
```

### Add New Tax
```
Admin → Pricing Rules → Add Pricing Rule
Name, Type: Markup, Value, Is Percentage → Save
```

### Create Discount
```
Admin → Pricing Rules → Add Pricing Rule
Name, Type: Discount, Value, Dates → Save
```

### Deactivate Rule
```
Admin → Pricing Rules → Select Rule
Uncheck "Is Active" → Save
```

---

## 📖 Additional Resources

### Related Documentation
- `TAX_IMPLEMENTATION_GUIDE.md` - Technical details
- `TAX_QUICK_ANSWER.md` - Quick overview
- Django Admin Documentation: https://docs.djangoproject.com/en/stable/ref/contrib/admin/

### Video Tutorials
(To be created)
- How to change GST rate
- Creating promotional discounts
- Bulk operations

---

**Remember:** All changes apply immediately. No code deployment or server restart needed!

**Questions?** Contact your technical team or refer to the troubleshooting section.

---

**Document Version:** 1.0  
**Last Updated:** February 17, 2026  
**Next Review:** March 2026
