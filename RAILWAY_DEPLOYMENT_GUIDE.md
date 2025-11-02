# Seller Motivation Detector AI - Railway Deployment Guide

## 🚀 Quick Start (10 Minutes)

This guide will help you deploy the Seller Motivation Detector AI to Railway.app's free tier.

---

## Step 1: Create Railway Account

1. Go to **https://railway.app**
2. Click "Start a New Project"
3. Sign up with GitHub (recommended) or email
4. Verify your email

---

## Step 2: Deploy from GitHub

### Option A: Deploy from GitHub (Recommended)

1. Create a new GitHub repository:
   - Go to https://github.com/new
   - Name it: `seller-motivation-detector-ai`
   - Make it Private
   - Don't initialize with README
   - Click "Create repository"

2. Push the code to GitHub:
   ```bash
   cd /path/to/railway-deployment
   git remote add origin https://github.com/YOUR_USERNAME/seller-motivation-detector-ai.git
   git branch -M main
   git push -u origin main
   ```

3. In Railway:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select your `seller-motivation-detector-ai` repository
   - Railway will automatically detect it's a Python/Flask app

### Option B: Deploy from Local Files (Easier)

1. In Railway dashboard:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Click "Deploy from GitHub repo" again
   - OR use Railway CLI (see below)

### Option C: Use Railway CLI

1. In your terminal (in the railway-deployment folder):
   ```bash
   railway login
   railway init
   railway up
   ```

---

## Step 3: Configure Environment Variables

1. In Railway dashboard, click on your deployed service
2. Go to "Variables" tab
3. Add these environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   
   FLASK_ENV=production
   ```
4. Click "Add" for each variable

---

## Step 4: Get Your Public URL

1. In Railway dashboard, go to "Settings" tab
2. Scroll to "Networking" section
3. Click "Generate Domain"
4. Railway will give you a URL like: `seller-motivation-detector-production.up.railway.app`
5. **Copy this URL** - you'll need it for WordPress!

---

## Step 5: Test Your Deployment

1. Visit your Railway URL
2. You should see the Seller Motivation Detector interface
3. Paste a test conversation and click "Analyze"
4. Verify the analysis works and PDF export works

---

## Step 6: Create WordPress Resource Post

1. Log into WordPress admin: https://base.realestatecommando.com/wp-admin
2. Go to "Resources" (custom post type)
3. Click "Add New"
4. Title: **"Seller Motivation Detector AI"**
5. In the content editor, add this iframe code:

```html
<style>
.motivation-detector-container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
}
.motivation-detector-iframe {
    width: 100%;
    height: 1400px;
    border: none;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
@media (max-width: 768px) {
    .motivation-detector-iframe {
        height: 1600px;
    }
}
</style>

<div class="motivation-detector-container">
    <iframe 
        src="https://YOUR-RAILWAY-URL.up.railway.app" 
        class="motivation-detector-iframe"
        title="Seller Motivation Detector AI">
    </iframe>
</div>
```

6. Replace `YOUR-RAILWAY-URL` with your actual Railway URL
7. Set the slug to: `seller-motivation-detector-ai`
8. Publish!

---

## Step 7: Set Up WP Fusion Access Control

1. In the WordPress post editor, find the WP Fusion meta box
2. Select "Protect this content"
3. Choose the tag(s) that should have access (e.g., "AI Tools Access", "Premium Member")
4. Set redirect URL to your purchase page if user doesn't have access
5. Update the post

---

## Step 8: Test Everything

1. **Test as logged-out user:**
   - Visit: https://base.realestatecommando.com/resources/seller-motivation-detector-ai/
   - Should redirect to purchase page

2. **Test as member without access:**
   - Log in as test user without the required tag
   - Should redirect to purchase page

3. **Test as authorized member:**
   - Log in as user with the required tag
   - Should see the tool and be able to use it

4. **Test the tool functionality:**
   - Paste a seller conversation
   - Click "Analyze Seller Motivation"
   - Verify results appear
   - Click "Download PDF Report"
   - Verify PDF downloads correctly

---

## 🎉 You're Done!

Your Seller Motivation Detector AI is now:
- ✅ Deployed to Railway (free tier)
- ✅ Integrated with WordPress
- ✅ Protected by WP Fusion tags
- ✅ Using your OpenAI API key
- ✅ Live for your members!

---

## 💰 Cost Breakdown

**Railway Free Tier:**
- 500 execution hours/month (enough for 24/7)
- $5/GB outbound data transfer
- Typically stays free for small to medium usage

**OpenAI API:**
- ~$0.002 per analysis
- 100 users × 2 analyses/day = ~$12/month

**Total: ~$12/month** (or less if you stay in Railway free tier)

---

## 🔧 Troubleshooting

### App won't start
- Check Railway logs in dashboard
- Verify environment variables are set correctly
- Make sure OPENAI_API_KEY is valid

### Tool not loading in WordPress
- Check that iframe URL is correct
- Verify Railway app is running (check dashboard)
- Check browser console for errors

### WP Fusion not working
- Verify tag is applied to user account
- Check WP Fusion settings on the post
- Test with different user accounts

---

## 📞 Need Help?

If you run into issues:
1. Check Railway logs in dashboard
2. Check WordPress error logs
3. Test the Railway URL directly (outside WordPress)
4. Let me know and I can help troubleshoot!

---

## 🚀 Next Steps

Once this is working:
1. Deploy the Deal Analyzer AI the same way
2. Build the Offer Creator AI (Tool #3)
3. Create an AI Tools bundle for members
4. Profit! 💰
