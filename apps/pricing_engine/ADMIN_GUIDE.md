# Pricing Engine Admin Guide

**Version**: 1.0.0  
**Date**: February 22, 2026  
**For**: System Administrators

---

## Overview

The Pricing Engine allows you to configure all pricing parameters for the Shambit Travel platform through the Django Admin interface. No code changes are required to adjust prices, taxes, fees, or pricing rules.

---

## Accessing the Admin Interface

1. Navigate to: `https://your-domain.com/admin/`
2. Login with your admin credentials
3. Go to: **Pricing Engine** section

You'll see two main sections:
- **Pricing Configuration** - Global pricing settings (singleton)
- **Pricing Rules** - Individual pricing rules (taxes, discounts, etc.)

---

## Pricing Configuration

### What is it?
A singleton configuration that controls global pricing behavior. Only one instance exists.

### How to Access
1. Go to: **Pricing Engine → Pricing Configuration**
2. Click on the existing configuration (or it will be created automatically)

### Configuration Sections

#### 1. Age-Based Pricing

**Chargeable Age Threshold**
- **What it does**: Sets the minimum age for chargeable travelers
- **Default**: 5 years
- **Range**: 0-18 years
- **Example**: If set to 5, children under 5 years old travel free
- **Use case**: Family-friendly pricing, encourage bookings with children

**How to change**:
1. Enter new age (e.g., 6 for "under 6 free")
2. Click "Save"
3. All future bookings will use the new threshold

---

#### 2. Tax & Fee Configuration (Phase 3)

**GST Rate**
- **What it does**: Sets the Goods and Services Tax percentage
- **Default**: 18.00%
- **Range**: 0-100%
- **Example**: 18% is the standard GST rate in India
- **Use case**: Comply with tax regulations, adjust for tax changes

**Platform Fee Rate**
- **What it does**: Sets the platform service fee percentage
- **Default**: 2.00%
- **Range**: 0-100%
- **Example**: 2% platform fee on all bookings
- **Use case**: Revenue generation, service charges

**How to change**:
1. Enter new percentage (e.g., 12.00 for 12% GST)
2. Click "Save"
3. All future price calculations will use the new rates

**Important**: Tax changes may require legal compliance review.

---

#### 3. Price Lock & Change Detection (Phase 3)

**Price Lock Duration**
- **What it does**: How long prices are locked after calculation
- **Default**: 15 minutes
- **Range**: 5-60 minutes
- **Example**: User has 15 minutes to complete booking at locked price
- **Use case**: Balance between price stability and market changes

**Price Change Alert Threshold**
- **What it does**: Alert admins if price changes by more than this percentage
- **Default**: 5.00%
- **Range**: 0-100%
- **Example**: Alert if price changes by more than 5% between preview and booking
- **Use case**: Detect pricing errors, monitor market volatility

**Enable Price Change Alerts**
- **What it does**: Turn admin alerts on/off
- **Default**: Enabled (True)
- **Example**: Disable during maintenance or testing
- **Use case**: Control alert noise

**How to use**:
1. Set threshold (e.g., 5% for moderate sensitivity)
2. Enable/disable alerts as needed
3. Monitor admin notifications for significant changes

---

#### 4. Weekend & Seasonal Pricing

**Default Weekend Multiplier**
- **What it does**: Multiplies prices for weekend bookings
- **Default**: 1.3 (30% increase)
- **Range**: 1.0-3.0
- **Example**: 1.5 = 50% weekend surcharge
- **Use case**: Peak demand pricing, maximize revenue

**Weekend Days**
- **What it does**: Defines which days are considered weekends
- **Default**: [4, 5, 6] (Friday, Saturday, Sunday)
- **Format**: JSON array, 0=Monday, 6=Sunday
- **Example**: [5, 6] for Saturday-Sunday only
- **Use case**: Regional weekend definitions

**Seasonal Pricing Rules**
- **What it does**: Apply multipliers for specific date ranges
- **Format**: JSON object
- **Example**:
  ```json
  {
    "summer": {
      "start": "06-01",
      "end": "08-31",
      "multiplier": 1.2
    },
    "winter": {
      "start": "12-01",
      "end": "02-28",
      "multiplier": 0.9
    }
  }
  ```
- **Use case**: Peak season pricing, off-season discounts

**How to configure**:
1. Set weekend multiplier (e.g., 1.4 for 40% increase)
2. Define weekend days as JSON array
3. Add seasonal rules as JSON object
4. Click "Save"

---

#### 5. Booking Policies

**Minimum Advance Booking Days**
- **What it does**: Minimum days in advance for booking
- **Default**: 1 day
- **Range**: 0-365 days
- **Example**: 2 = must book at least 2 days ahead
- **Use case**: Operational planning, prevent last-minute bookings

**Maximum Advance Booking Days**
- **What it does**: Maximum days in advance for booking
- **Default**: 365 days
- **Range**: 1-730 days
- **Example**: 180 = can book up to 6 months ahead
- **Use case**: Inventory management, pricing stability

**How to configure**:
1. Set minimum days (e.g., 3 for 3-day advance notice)
2. Set maximum days (e.g., 365 for 1 year ahead)
3. Click "Save"

---

## Pricing Rules

### What are they?
Individual rules that apply markups or discounts to packages. Multiple rules can be active simultaneously.

### How to Access
1. Go to: **Pricing Engine → Pricing Rules**
2. Click "Add Pricing Rule" to create new
3. Click on existing rule to edit

### Creating a Pricing Rule

#### Basic Information

**Name**
- **Example**: "GST 18%", "Early Bird Discount", "Peak Season Surcharge"
- **Purpose**: Identify the rule in admin and reports

**Description**
- **Example**: "Goods and Services Tax as per Indian tax law"
- **Purpose**: Explain the rule's purpose and legal basis

**Rule Type**
- **MARKUP**: Increases price (taxes, fees, surcharges)
- **DISCOUNT**: Decreases price (promotions, offers)

**Value**
- **Format**: Decimal number
- **Example**: 18.00 for 18%, or 500 for ₹500 fixed amount

**Is Percentage**
- **True**: Value is a percentage (e.g., 18%)
- **False**: Value is a fixed amount (e.g., ₹500)

#### Applicability

**Target Package**
- **Leave blank**: Apply to ALL packages
- **Select package**: Apply to specific package only
- **Example**: "Mumbai Explorer" for Mumbai-specific discount

**Is Active**
- **True**: Rule is currently active
- **False**: Rule is disabled (but not deleted)
- **Use case**: Temporarily disable rules without deleting

#### Validity Period

**Active From**
- **Format**: Date and time
- **Example**: 2026-03-01 00:00:00
- **Purpose**: When the rule starts applying

**Active To**
- **Leave blank**: Rule never expires
- **Set date**: Rule expires on this date
- **Example**: 2026-12-31 23:59:59 for year-end promotion

### Example Pricing Rules

#### 1. GST (Tax)
```
Name: GST 18%
Description: Goods and Services Tax
Rule Type: MARKUP
Value: 18.00
Is Percentage: True
Target Package: (blank - all packages)
Active From: 2026-01-01 00:00:00
Active To: (blank - never expires)
Is Active: True
```

#### 2. Platform Fee
```
Name: Platform Service Fee
Description: Platform maintenance and support fee
Rule Type: MARKUP
Value: 2.00
Is Percentage: True
Target Package: (blank - all packages)
Active From: 2026-01-01 00:00:00
Active To: (blank - never expires)
Is Active: True
```

#### 3. Early Bird Discount
```
Name: Early Bird 10% Off
Description: Book 30+ days in advance
Rule Type: DISCOUNT
Value: 10.00
Is Percentage: True
Target Package: (blank - all packages)
Active From: 2026-03-01 00:00:00
Active To: 2026-06-30 23:59:59
Is Active: True
```

#### 4. Mumbai Special Offer
```
Name: Mumbai Package Discount
Description: Special promotion for Mumbai packages
Rule Type: DISCOUNT
Value: 500.00
Is Percentage: False (fixed ₹500 off)
Target Package: Mumbai Explorer
Active From: 2026-03-01 00:00:00
Active To: 2026-03-31 23:59:59
Is Active: True
```

---

## Common Tasks

### Task 1: Change GST Rate

**Scenario**: Government changes GST from 18% to 12%

**Steps**:
1. Go to: **Pricing Engine → Pricing Configuration**
2. Find: **GST Rate** field
3. Change: 18.00 → 12.00
4. Click: **Save**
5. Verify: Calculate a test price to confirm

**Impact**: All future bookings will use 12% GST

---

### Task 2: Create Seasonal Promotion

**Scenario**: 20% off all packages for summer (June-August)

**Steps**:
1. Go to: **Pricing Engine → Pricing Rules**
2. Click: **Add Pricing Rule**
3. Fill in:
   - Name: "Summer Sale 20% Off"
   - Description: "Summer promotion for all packages"
   - Rule Type: DISCOUNT
   - Value: 20.00
   - Is Percentage: True
   - Target Package: (leave blank)
   - Active From: 2026-06-01 00:00:00
   - Active To: 2026-08-31 23:59:59
   - Is Active: True
4. Click: **Save**

**Impact**: 20% discount applied to all packages from June 1 to August 31

---

### Task 3: Disable Weekend Pricing

**Scenario**: Remove weekend surcharge temporarily

**Steps**:
1. Go to: **Pricing Engine → Pricing Configuration**
2. Find: **Default Weekend Multiplier**
3. Change: 1.3 → 1.0 (no surcharge)
4. Click: **Save**

**Impact**: No weekend surcharge until changed back

---

### Task 4: Set Price Change Alerts

**Scenario**: Get notified if prices change by more than 3%

**Steps**:
1. Go to: **Pricing Engine → Pricing Configuration**
2. Find: **Price Change Alert Threshold**
3. Change: 5.00 → 3.00
4. Ensure: **Enable Price Change Alerts** is checked
5. Click: **Save**

**Impact**: Admin receives alerts for price changes > 3%

---

## Monitoring & Reports

### Price Calculation Logs

**Location**: Django Admin → Audit Logs → Price Calculations

**Information**:
- User who requested price
- Package and components selected
- Calculated price
- Timestamp
- IP address
- Success/failure status

**Use case**: Audit trail, debugging, compliance

### Price Change Alerts

**Location**: Admin notifications (email/dashboard)

**Triggered when**:
- Price changes exceed threshold
- Between preview and booking
- Significant market changes

**Contains**:
- Package name
- Old price vs new price
- Percentage change
- Timestamp
- User information

**Action**: Review and investigate significant changes

---

## Best Practices

### 1. Test Before Applying
- Use staging environment for testing
- Calculate test prices before going live
- Verify tax calculations with accountant

### 2. Document Changes
- Keep a log of pricing changes
- Note reasons for changes
- Track effective dates

### 3. Monitor Impact
- Watch booking rates after changes
- Monitor revenue impact
- Collect customer feedback

### 4. Legal Compliance
- Consult legal team for tax changes
- Ensure price transparency
- Display all charges clearly

### 5. Gradual Changes
- Don't make drastic price changes
- Test with small segments first
- Monitor customer response

---

## Troubleshooting

### Issue: Prices not updating

**Possible causes**:
1. Configuration not saved
2. Browser cache
3. Old pricing rules still active

**Solutions**:
1. Verify configuration saved successfully
2. Clear browser cache and refresh
3. Check active pricing rules
4. Verify rule validity periods

---

### Issue: Wrong tax calculation

**Possible causes**:
1. Incorrect GST rate
2. Multiple tax rules active
3. Rule applicability issue

**Solutions**:
1. Check GST rate in configuration
2. Review all active pricing rules
3. Verify rule target packages
4. Check rule validity periods

---

### Issue: Price change alerts not working

**Possible causes**:
1. Alerts disabled
2. Threshold too high
3. Email configuration issue

**Solutions**:
1. Check "Enable Price Change Alerts" is True
2. Lower threshold (e.g., 3% instead of 5%)
3. Verify email settings in Django config
4. Check admin notification preferences

---

## Support

### Getting Help
- **Technical Issues**: Contact development team
- **Pricing Strategy**: Contact business team
- **Legal/Tax Questions**: Contact legal/accounting team

### Documentation
- **Developer Guide**: `PRICING_DEVELOPER_GUIDE.md`
- **API Documentation**: `/api/docs/`
- **Security Analysis**: `PRICING_SECURITY_ANALYSIS.md`

---

**Last Updated**: February 22, 2026  
**Version**: 1.0.0  
**Maintained by**: Shambit Development Team

