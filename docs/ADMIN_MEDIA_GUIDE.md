# Admin Media Management Guide
## Complete Guide for Content Managers

**Target Audience:** Admins, Content Managers, Marketing Team  
**Last Updated:** February 12, 2026

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Uploading Media](#uploading-media)
3. [Organizing Media](#organizing-media)
4. [Best Practices for Customer Retention](#best-practices-for-customer-retention)
5. [SEO Optimization](#seo-optimization)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Features](#advanced-features)

---

## Quick Start

### Accessing Media Library

1. Go to Django Admin: `https://your-domain.com/admin/`
2. Login with your admin credentials
3. Navigate to **Media Library** → **Media**

### Your First Upload

1. Click **"Add Media"** button
2. Choose file (max 5MB for images)
3. Fill in:
   - **Title**: "Varanasi Ganga Aarti Evening Ceremony"
   - **Alt Text**: "Priests performing evening Ganga Aarti with oil lamps at Dashashwamedh Ghat"
   - **Content Type**: Select "city | city"
   - **Object ID**: Enter the city ID (e.g., 5 for Varanasi)
4. Click **"Save"**

✅ Done! Your image is now live and will appear on the city page.

---

## Uploading Media

### File Requirements

#### Images
- **Formats**: JPEG, PNG, GIF, WebP
- **Max Size**: 5MB
- **Recommended Size**: 1920x1080px (Full HD)
- **Aspect Ratios**:
  - Hero images: 16:9 (landscape)
  - Thumbnails: 4:3 or 1:1 (square)
  - Mobile: 9:16 (portrait)

#### Videos
- **Formats**: MP4, AVI, MOV, WMV, FLV
- **Max Size**: 50MB
- **Recommendation**: Use YouTube/Vimeo for videos (saves bandwidth)

#### Documents
- **Formats**: PDF
- **Max Size**: 10MB

### Upload Methods

#### Method 1: Single Upload (Django Admin)
1. Go to **Media Library** → **Add Media**
2. Click **"Choose File"**
3. Select image from your computer
4. Fill in metadata (title, alt text)
5. Select content type and object ID
6. Click **"Save"**

#### Method 2: Bulk Upload (API)
```bash
# Upload multiple files at once
curl -X POST "https://your-domain.com/api/media/bulk_upload/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg" \
  -F "content_type=cities.city" \
  -F "object_id=5"
```

### Image Optimization Before Upload

**Why optimize?**
- Faster page loading (better customer experience)
- Lower bandwidth usage (stay within Cloudinary free tier)
- Better SEO rankings (Google loves fast sites)

**How to optimize:**

1. **Resize Large Images**
   - Use online tools: [TinyPNG](https://tinypng.com), [Squoosh](https://squoosh.app)
   - Target: 1920x1080px for hero images, 800x600px for thumbnails
   - Don't go below 800px width (quality suffers)

2. **Compress Images**
   - JPEG: 80-85% quality (sweet spot)
   - PNG: Use for logos/graphics only (3x larger than JPEG)
   - WebP: Best format, but not all tools support it

3. **Rename Files**
   - ✅ Good: `varanasi-ganga-aarti-evening.jpg`
   - ❌ Bad: `IMG_1234.jpg`, `DSC_5678.jpg`
   - Use hyphens, not underscores
   - Include location and activity keywords

---

## Organizing Media

### Content Types

Media can be attached to different content types:

#### 1. Cities (`cities.city`)
- **Use for**: City hero images, landmarks, attractions
- **Example**: Varanasi ghats, Taj Mahal, Gateway of India
- **How to find Object ID**: Go to Cities → Click city → Check URL (e.g., `/admin/cities/city/5/` → ID is 5)

#### 2. Packages (`packages.package`)
- **Use for**: Package featured images, itinerary photos
- **Example**: "Varanasi Spiritual Tour" package images
- **How to find Object ID**: Go to Packages → Click package → Check URL

#### 3. Experiences (`packages.experience`)
- **Use for**: Activity photos, experience thumbnails
- **Example**: Boat ride, temple visit, cooking class
- **How to find Object ID**: Go to Experiences → Click experience → Check URL

#### 4. Articles (`articles.article`)
- **Use for**: Blog post featured images, inline images
- **Example**: "Top 10 Things to Do in Varanasi" header image
- **How to find Object ID**: Go to Articles → Click article → Check URL

### Tagging Strategy

**Good tagging helps you find media later!**

#### Title Format
```
[Location] - [Activity] - [Detail]

Examples:
✅ "Varanasi - Ganga Aarti - Evening Ceremony"
✅ "Taj Mahal - Sunrise - Front View"
✅ "Jaipur - Hawa Mahal - Architectural Detail"

❌ "IMG_1234"
❌ "Photo"
❌ "Untitled"
```

#### Alt Text Format
```
[What's happening] at [Location], [Additional context]

Examples:
✅ "Priests performing evening Ganga Aarti ceremony with oil lamps at Dashashwamedh Ghat, Varanasi"
✅ "Sunrise view of Taj Mahal reflecting in Yamuna River, Agra"
✅ "Intricate pink sandstone facade of Hawa Mahal palace, Jaipur"

❌ "Image"
❌ "Photo of Varanasi"
❌ "" (empty)
```

### Bulk Operations

#### Update Metadata for Multiple Files
1. Go to **Media Library** → **Media**
2. Select multiple media files (checkboxes)
3. Choose action: **"Update metadata"**
4. Enter new alt text or title
5. Click **"Go"**

#### Delete Multiple Files
1. Select files to delete
2. Choose action: **"Delete selected media"**
3. Confirm deletion
4. Files are removed from Cloudinary and database

---

## Best Practices for Customer Retention

### 1. Visual Quality = Trust

**Why it matters:**
- High-quality images = professional business
- Poor images = customers leave
- 75% of customers judge credibility by website design

**What to do:**
- Use professional photos (hire photographer if needed)
- Ensure good lighting (natural light is best)
- Show real experiences (not stock photos)
- Update photos regularly (seasonal changes)

### 2. Loading Speed = Conversions

**Why it matters:**
- 1 second delay = 7% loss in conversions
- 53% of mobile users abandon slow sites
- Google ranks fast sites higher

**What to do:**
- Optimize images before upload (max 2MB)
- Use Cloudinary optimization (automatic)
- Don't upload RAW images (10MB+)
- Delete unused media regularly

### 3. SEO = More Customers

**Why it matters:**
- Images appear in Google Image Search
- Alt text helps visually impaired users
- Proper tagging improves rankings

**What to do:**
- Write descriptive alt text (50-125 characters)
- Include location keywords
- Use descriptive file names
- Add captions where relevant

### 4. Consistency = Brand Recognition

**Why it matters:**
- Consistent style = professional brand
- Random styles = confusing experience
- Brand recognition = customer loyalty

**What to do:**
- Use similar color grading
- Maintain consistent aspect ratios
- Follow brand guidelines
- Create style guide for photographers

---

## SEO Optimization

### Image SEO Checklist

For every image you upload:

- [ ] **Descriptive filename** (varanasi-ganga-aarti.jpg)
- [ ] **Meaningful title** (Varanasi Ganga Aarti Evening Ceremony)
- [ ] **Detailed alt text** (50-125 characters)
- [ ] **Proper content type** (linked to city/package/article)
- [ ] **Optimized file size** (<2MB)
- [ ] **Correct dimensions** (1920x1080 for hero, 800x600 for thumbnails)

### Alt Text Best Practices

**Good Alt Text:**
```
"Priests performing evening Ganga Aarti ceremony with oil lamps at Dashashwamedh Ghat, Varanasi, with crowds of devotees watching from the riverbank"
```

**Why it's good:**
- Describes what's happening (Ganga Aarti ceremony)
- Includes location (Dashashwamedh Ghat, Varanasi)
- Adds context (evening, oil lamps, crowds)
- Natural language (not keyword stuffing)
- 50-125 characters (optimal length)

**Bad Alt Text:**
```
"Varanasi Ganga Aarti ceremony temple India Hindu religion spiritual tourism travel destination best places to visit"
```

**Why it's bad:**
- Keyword stuffing (Google penalizes this)
- Unnatural language
- Too long (>125 characters)
- Doesn't describe the image

### Title Best Practices

**Good Title:**
```
"Varanasi Ganga Aarti Evening Ceremony"
```

**Why it's good:**
- Concise (5-7 words)
- Includes location (Varanasi)
- Describes activity (Ganga Aarti)
- Adds context (Evening Ceremony)

**Bad Title:**
```
"IMG_1234"
```

**Why it's bad:**
- No descriptive information
- No keywords
- Doesn't help SEO
- Hard to find later

---

## Troubleshooting

### Issue: "Upload failed"

**Possible causes:**
1. File too large (>5MB for images, >50MB for videos)
2. Invalid file format
3. Network timeout

**Solutions:**
1. Compress image using TinyPNG or Squoosh
2. Check file extension (.jpg, .png, .gif, .webp)
3. Try again with stable internet connection

### Issue: "Image not appearing on website"

**Possible causes:**
1. Wrong content type selected
2. Wrong object ID entered
3. Content not published
4. Cache not cleared

**Solutions:**
1. Verify content type matches (e.g., "cities.city" for cities)
2. Double-check object ID in URL
3. Ensure city/package/article is published (not draft)
4. Clear browser cache (Ctrl+Shift+R)

### Issue: "Image loads slowly"

**Possible causes:**
1. Image too large (>2MB)
2. Not optimized
3. Not using Cloudinary

**Solutions:**
1. Compress image before upload
2. Ensure Cloudinary is enabled (check with tech team)
3. Use JPEG instead of PNG for photos

### Issue: "Can't find uploaded image"

**Possible causes:**
1. Not linked to content
2. Orphaned media
3. Deleted by mistake

**Solutions:**
1. Go to Media Library → Search by title
2. Check "Orphaned Media" section
3. Contact tech team for recovery (if recently deleted)

---

## Advanced Features

### Media Statistics

**View usage stats:**
1. Go to **Media Library** → **Dashboard**
2. See:
   - Total files uploaded
   - Storage used
   - Bandwidth used this month
   - Recent uploads
   - Files by content type

**Why it matters:**
- Monitor Cloudinary free tier usage (25GB storage, 25GB bandwidth/month)
- Identify unused media
- Track upload trends

### Cleanup Operations

#### Find Orphaned Media
**What are orphaned media?**
- Files not linked to any content
- Uploaded but never used
- Linked to deleted content

**How to find:**
1. Go to **Media Library** → **Orphaned Media**
2. Review list of unlinked files
3. Either:
   - Link to content (edit media, add content type + object ID)
   - Delete if not needed

#### Remove Unused Files
**What are unused files?**
- Files in Cloudinary but not in database
- Leftover from failed uploads
- Manually uploaded to Cloudinary

**How to remove:**
1. Run cleanup command (ask tech team):
   ```bash
   python manage.py cleanup_media --unused
   ```
2. Review list of files to be deleted
3. Confirm deletion

### Search and Filter

**Search by:**
- Title (e.g., "Varanasi")
- Alt text (e.g., "Ganga Aarti")
- File type (image, video, document)
- Content type (cities, packages, articles)
- Date range (uploaded between X and Y)

**How to search:**
1. Go to **Media Library** → **Media**
2. Use search box at top
3. Apply filters on right sidebar
4. Click **"Search"**

### Bulk Download

**Download multiple files:**
1. Select files (checkboxes)
2. Choose action: **"Download selected"**
3. Files are zipped and downloaded

**Use cases:**
- Backup before major changes
- Share with marketing team
- Archive old media

---

## Weekly Maintenance Checklist

### Every Monday (15 minutes)

- [ ] Review last week's uploads (check quality)
- [ ] Find and link orphaned media
- [ ] Delete unused/duplicate files
- [ ] Check storage usage (should be <50% of 25GB)
- [ ] Update alt text for recent uploads (if missing)

### Every Month (30 minutes)

- [ ] Audit all media for quality
- [ ] Update outdated photos (seasonal changes)
- [ ] Check bandwidth usage (should be <25GB/month)
- [ ] Review SEO performance (Google Search Console)
- [ ] Archive old media (if needed)

### Every Quarter (1 hour)

- [ ] Comprehensive media audit
- [ ] Update brand guidelines
- [ ] Train new team members
- [ ] Review customer feedback on images
- [ ] Plan new photo shoots

---

## Customer Retention Strategies

### 1. Seasonal Updates

**Why it matters:**
- Customers want current information
- Seasonal photos show you care
- Increases repeat visits

**What to do:**
- Update hero images every season
- Add festival photos during peak times
- Show weather-appropriate images
- Highlight seasonal activities

### 2. User-Generated Content

**Why it matters:**
- Authentic experiences build trust
- Social proof increases conversions
- Free content from customers

**What to do:**
- Ask customers to share photos
- Feature best photos on website
- Give credit to photographers
- Run photo contests

### 3. Behind-the-Scenes

**Why it matters:**
- Humanizes your brand
- Builds emotional connection
- Shows transparency

**What to do:**
- Share team photos
- Show preparation process
- Document local partnerships
- Highlight community involvement

### 4. Before/After Comparisons

**Why it matters:**
- Shows transformation
- Demonstrates value
- Creates emotional impact

**What to do:**
- Sunrise vs. sunset photos
- Seasonal changes
- Renovation progress
- Customer testimonials with photos

---

## Success Metrics

### Track These Numbers

1. **Page Load Time**
   - Target: <3 seconds
   - Tool: Google PageSpeed Insights
   - Impact: Faster = more conversions

2. **Bounce Rate**
   - Target: <40%
   - Tool: Google Analytics
   - Impact: Lower = better engagement

3. **Image Search Traffic**
   - Target: 10% of total traffic
   - Tool: Google Search Console
   - Impact: More traffic = more bookings

4. **Conversion Rate**
   - Target: >2%
   - Tool: Google Analytics
   - Impact: Higher = more revenue

### Monthly Report Template

```
Media Performance Report - [Month Year]

1. Uploads
   - Total files uploaded: X
   - Images: X | Videos: X | Documents: X
   - Average file size: X MB

2. Storage
   - Total storage used: X GB / 25 GB (X%)
   - Bandwidth used: X GB / 25 GB (X%)
   - Status: ✅ Within free tier / ⚠️ Approaching limit

3. Performance
   - Average page load time: X seconds
   - Bounce rate: X%
   - Image search traffic: X visits

4. Actions Taken
   - Orphaned media cleaned: X files
   - Unused files removed: X files
   - Alt text updated: X files
   - New uploads: X files

5. Next Month Goals
   - [ ] Goal 1
   - [ ] Goal 2
   - [ ] Goal 3
```

---

## Support

**Need help?**
- Technical issues: Contact tech team
- Content questions: Contact content manager
- Training: Schedule 1-on-1 session

**Resources:**
- Django Admin: `/admin/media_library/`
- API Docs: `/swagger/`
- Cloudinary Dashboard: https://cloudinary.com/console
- This guide: `/docs/ADMIN_MEDIA_GUIDE.md`
