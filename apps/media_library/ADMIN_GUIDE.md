# Media Library Admin Guide

## Overview

The Media Library is the central system for managing all images, videos, and documents used across your travel platform. This guide will help you understand how to upload, organize, and use media effectively.

---

## Allowed File Types

### 📷 Images
- **Formats**: JPG, JPEG, PNG, GIF, WebP
- **Maximum Size**: 5 MB
- **Best For**: City photos, article images, package galleries, hero images
- **Recommended**: Use JPG for photos, PNG for graphics with transparency

### 🎥 Videos
- **Formats**: MP4, MOV, AVI, WMV, FLV
- **Maximum Size**: 50 MB
- **Best For**: Experience previews, tour walkthroughs, destination highlights
- **Recommended**: Use MP4 for best compatibility

### 📄 Documents
- **Formats**: PDF
- **Maximum Size**: 10 MB
- **Best For**: Brochures, itineraries, terms and conditions, booking confirmations
- **Recommended**: Compress PDFs before uploading

---

## How to Upload Media

### Step 1: Navigate to Media Library
1. Log in to the admin panel
2. Click on "Media Library" in the left sidebar
3. Click "Add Media" button in the top right

### Step 2: Upload Your File
1. Click "Choose File" button
2. Select your image, video, or document
3. Wait for the file to upload

### Step 3: Add Information
1. **Title** (Required): Give your media a descriptive title
   - Example: "Paris Eiffel Tower Sunset View"
   - This helps you find the file later

2. **Alt Text** (Recommended): Describe what's in the image
   - Example: "Eiffel Tower at sunset with orange sky"
   - Important for accessibility and SEO
   - Screen readers use this to describe images to visually impaired users

3. **Attach to Content** (Optional): Link this media to specific content
   - Select content type (City, Article, or Package)
   - Enter the ID of the item
   - You can find IDs in the respective admin sections

### Step 4: Save
Click "Save" to upload your media

---

## Understanding the Media List

### Thumbnail Preview
- Shows a small preview of images
- File type icon for videos and documents
- ⚠️ icon if there's an error loading the file

### Title / Filename
- **Bold text**: Your custom title
- **Gray text below**: Original filename

### Type Badge
- **Green (Image)**: Photo or graphic file
- **Blue (Video)**: Video file
- **Red (Document)**: PDF document
- **Gray (Other)**: Other file types

### File Size
- Shows how much storage space the file uses
- Helps identify large files that might need optimization

### Attached To
- **📎 with link**: Media is attached to specific content (click to view)
- **🔓 Not attached**: Media is available but not linked to any content
- Shows the content type and ID for reference

### Upload Date
- When the file was uploaded to the system

---

## Understanding File Information

When you view or edit a media file, you'll see detailed information:

### File Details
- **File Name**: Original name of the uploaded file
- **File Type**: Extension (JPG, MP4, PDF, etc.)
- **File Size**: How much space it uses (KB, MB, GB)

### Storage Location
- **☁️ Cloudinary (Cloud Storage)**: File is stored in the cloud (recommended)
  - Faster loading
  - Automatic optimization
  - Worldwide CDN delivery
  - Responsive images automatically generated

- **💾 Local Server Storage**: File is stored on the server
  - May be slower for users far from server
  - Requires manual optimization

### Image-Specific Information (for images only)
- **Dimensions**: Width × Height in pixels
- **Image Format**: JPEG, PNG, GIF, etc.
- **Color Mode**: RGB, RGBA, etc.

### Upload Information
- **Uploaded**: Date and time when file was added

### Usage Tip
- Shows how to use the file in your content
- For Cloudinary images, mentions automatic responsive optimization

---

## Attaching Media to Content

### What Does "Attaching" Mean?
Attaching media links it to specific content (like a city, article, or package). This helps organize your media and makes it easy to find all images for a specific item.

### How to Attach Media

#### Option 1: During Upload
1. When uploading, select "Attach to Content Type"
2. Choose City, Article, or Package
3. Enter the ID of the specific item
4. Save

#### Option 2: After Upload
1. Find the media in the list
2. Click to edit
3. Scroll to "Attachment" section
4. Select content type and enter ID
5. Save

### Finding Content IDs
- **Cities**: Go to Cities admin, the ID is in the URL or first column
- **Articles**: Go to Articles admin, the ID is in the URL or first column
- **Packages**: Go to Packages admin, the ID is in the URL or first column

### Example
To attach an image to Paris (City ID: 5):
1. Content Type: City
2. Content ID: 5
3. Save

Now this image is linked to Paris and will appear in Paris's media gallery.

---

## Best Practices

### Image Optimization
1. **Resize before upload**: Don't upload 10MB photos from your camera
2. **Use appropriate format**:
   - JPG for photos
   - PNG for graphics with transparency
   - WebP for modern browsers (best compression)
3. **Compress images**: Use tools like TinyPNG before uploading
4. **Recommended dimensions**:
   - Hero images: 1920×1080 pixels
   - Gallery images: 1200×800 pixels
   - Thumbnails: System generates automatically

### Naming Conventions
1. **Use descriptive titles**: "Paris Eiffel Tower Night" not "IMG_1234"
2. **Include location**: Helps with organization
3. **Be consistent**: Use similar naming patterns

### Alt Text Guidelines
1. **Be descriptive**: Describe what's in the image
2. **Keep it concise**: 1-2 sentences maximum
3. **Include context**: "Eiffel Tower at sunset" not just "tower"
4. **Don't say "image of"**: Screen readers already announce it's an image

### Organization Tips
1. **Attach media to content**: Makes it easier to find later
2. **Delete unused media**: Keeps library clean and saves storage
3. **Use meaningful titles**: You'll thank yourself later
4. **Regular cleanup**: Remove old or unused files monthly

---

## Responsive Images (Cloudinary)

### What Are Responsive Images?
When you upload images to Cloudinary, the system automatically creates multiple versions optimized for different devices:

- **Thumbnail**: Small preview (150×150)
- **Small**: Mobile phones (640px wide)
- **Medium**: Tablets (1024px wide)
- **Large**: Desktop (1920px wide)
- **Mobile**: High-DPI mobile (768px, 2x resolution)
- **Tablet**: High-DPI tablet (1024px, 2x resolution)

### Benefits
1. **Faster loading**: Smaller images for mobile devices
2. **Better quality**: Right size for each screen
3. **Automatic format**: WebP for modern browsers, JPG for older ones
4. **Bandwidth savings**: Users download only what they need
5. **No extra work**: System handles everything automatically

### How It Works
1. You upload one image
2. Cloudinary stores the original
3. When someone views your site, Cloudinary delivers the best version for their device
4. All versions are cached on CDN for fast delivery worldwide

---

## Troubleshooting

### Upload Failed
**Problem**: File won't upload
**Solutions**:
- Check file size (Images: 5MB, Videos: 50MB, Documents: 10MB)
- Verify file type is allowed
- Try a different browser
- Check your internet connection

### Can't Find Uploaded Media
**Problem**: Media uploaded but not visible
**Solutions**:
- Check the "All" tab (not filtered by type)
- Search by filename or title
- Check if it's attached to specific content

### Image Not Displaying
**Problem**: Image shows broken icon
**Solutions**:
- Check if file was actually uploaded
- Verify the file isn't corrupted
- Try re-uploading the file
- Contact support if issue persists

### Wrong Content Attached
**Problem**: Media attached to wrong item
**Solutions**:
- Edit the media
- Change the Content ID to correct one
- Or set to "Not attached" to unlink

### File Too Large
**Problem**: "File size too large" error
**Solutions**:
- Compress the file before uploading
- For images: Use TinyPNG or similar tool
- For videos: Use HandBrake or similar tool
- For PDFs: Use PDF compressor

---

## Bulk Operations

### Optimize Multiple Images
1. Select images using checkboxes
2. Choose "Optimize selected images" from Actions dropdown
3. Click "Go"
4. System will compress and optimize all selected images

### Generate Thumbnails
1. Select images using checkboxes
2. Choose "Generate thumbnails for selected images" from Actions dropdown
3. Click "Go"
4. System will create thumbnail versions

### Delete Multiple Files
1. Select files using checkboxes
2. Choose "Delete selected media" from Actions dropdown
3. Click "Go"
4. Confirm deletion

---

## Storage Information

### Cloudinary Free Tier Limits
- **Storage**: 25 GB
- **Bandwidth**: 25 GB/month
- **Transformations**: 25,000/month

### Monitoring Usage
1. Go to Media Library admin
2. Click "Media Dashboard" link
3. View current usage statistics
4. Check for alerts if approaching limits

### What Happens If Limits Exceeded?
- New uploads may fail
- Existing media continues to work
- Consider upgrading plan or cleaning up unused files

---

## Tips for Different Content Types

### City Images
- Upload hero image (wide landscape)
- Add gallery images (various angles)
- Include landmarks and attractions
- Show different times of day

### Article Images
- Featured image (1200×630 for social sharing)
- In-content images (support the story)
- Infographics (if applicable)
- Author photo (if needed)

### Package Images
- Main package image (eye-catching)
- Gallery of experiences included
- Accommodation photos
- Activity images

---

## Getting Help

### Need Assistance?
- Check this guide first
- Look at the help text in the admin interface
- Contact your system administrator
- Email support team

### Reporting Issues
When reporting problems, include:
1. What you were trying to do
2. What happened instead
3. Error message (if any)
4. Screenshot (if helpful)
5. Browser and device you're using

---

## Quick Reference

### File Type Limits
| Type | Formats | Max Size |
|------|---------|----------|
| Images | JPG, PNG, GIF, WebP | 5 MB |
| Videos | MP4, MOV, AVI, WMV, FLV | 50 MB |
| Documents | PDF | 10 MB |

### Required Fields
- ✅ File (must upload)
- ✅ Title (recommended, helps organization)
- ⚪ Alt Text (optional but important for accessibility)
- ⚪ Content Type (optional, for organization)
- ⚪ Content ID (optional, links to specific content)

### Keyboard Shortcuts
- `Ctrl/Cmd + S`: Save
- `Esc`: Cancel/Close
- `Tab`: Move to next field

---

## Glossary

**Alt Text**: Alternative text that describes an image for accessibility

**CDN**: Content Delivery Network - servers worldwide that deliver files quickly

**Cloudinary**: Cloud storage service for media files

**Content Type**: Category of content (City, Article, Package)

**Object ID**: Unique number identifying a specific item

**Responsive Images**: Different sized versions of an image for different devices

**Thumbnail**: Small preview version of an image

**Transformation**: Automatic image optimization and resizing

---

*Last Updated: [Current Date]*
*Version: 1.0*
