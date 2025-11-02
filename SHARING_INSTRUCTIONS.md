# 📤 How to Share Repository with Collaborators

## What "Shared with GitHub users" Means

When the assignment says "hosted in a GitHub repository shared with [usernames]", it means you need to:

1. **Add collaborators** to your repository so they can:
   - View the code
   - Clone the repository
   - Review the project
   - Potentially contribute or provide feedback

## GitHub Users to Share With:

1. **Naman-Bhalla** - https://github.com/Naman-Bhalla/
2. **raun** - https://github.com/raun/

---

## Step-by-Step Instructions

### Method 1: Add Collaborators via GitHub Web Interface (Recommended)

1. **Go to your repository**:
   - Visit: https://github.com/Piyanshu129/Web_scraper

2. **Click on "Settings"** (in the repository menu)

3. **Click on "Collaborators"** (left sidebar)

4. **Click "Add people"** button

5. **Search for each username**:
   - Type: `Naman-Bhalla`
   - Click "Add [username] to this repository"
   - Choose permission level: **Read** (recommended for reviewers)
   - Repeat for: `raun`

6. **GitHub will send invitations** to both users
   - They'll receive email notifications
   - They need to accept the invitations

### Method 2: Make Repository Public

If you want anyone to view it:

1. Go to repository **Settings**
2. Scroll down to **"Danger Zone"**
3. Click **"Change visibility"**
4. Select **"Make public"**
5. Confirm

⚠️ **Note**: This makes your code public to everyone. Only do this if you're comfortable with that.

### Method 3: Share Direct Links

You can also just share the repository URL:
- https://github.com/Piyanshu129/Web_scraper

But this requires the repository to be **public** for them to access it if they're not collaborators.

---

## Recommended Approach

**Best practice for assignment submissions**:
1. Add the specified users as **collaborators** with **Read** access
2. Keep repository **private** (more secure)
3. They'll be able to view and clone the repository
4. You maintain control over who can access it

---

## Quick Command Reference

If you prefer command line, you can also share via GitHub CLI (if installed):

```bash
# Install GitHub CLI first if not installed
# brew install gh

# Authenticate
gh auth login

# Add collaborators (requires GitHub CLI)
gh api repos/Piyanshu129/Web_scraper/collaborators/Naman-Bhalla -X PUT
gh api repos/Piyanshu129/Web_scraper/collaborators/raun -X PUT
```

But the web interface is easier for most people.

---

## Verification

After adding collaborators:
- They should appear in the "Collaborators" section
- They'll receive email invitations
- Once they accept, they can access your repository
- You can verify by checking Settings → Collaborators

---

## What the Reviewers Will See

Once shared, they can:
- ✅ View all source code
- ✅ Read README.md and documentation
- ✅ Clone the repository
- ✅ Review commit history
- ✅ See the project structure
- ✅ Test the code themselves

This is exactly what's needed for assignment evaluation!

