# Quick Migration Guide: Local PostgreSQL → Supabase

## 🎯 Step-by-Step Migration Process

### Step 1: Create Supabase Project (5 minutes)

1. **Sign up for Supabase**
   - Go to [https://supabase.com](https://supabase.com)
   - Click "Start your project" and sign up (GitHub/Google/Email)

2. **Create a new project**
   - Click "New Project"
   - Choose your organization (or create one)
   - Fill in project details:
     - **Project Name**: `mba-career-counselor` (or any name you like)
     - **Database Password**: Create a strong password **SAVE THIS!**
     - **Region**: Choose closest to you (e.g., `US East` for USA)
     - **Pricing Plan**: Select "Free" (500MB storage)
   - Click "Create new project"
   - ⏳ Wait 2-3 minutes for project to be ready

3. **Get your connection details**
   
   Once your project is ready:
   
   a. Click the **Settings** icon (⚙️) in the left sidebar
   
   b. Go to **Database** section
   
   c. Scroll down to **Connection string** section
   
   d. Select **Connection pooling** tab (recommended)
   
   e. You'll see a connection string like:
   ```
   postgresql://postgres.abcdefghij:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
   
   f. **Extract these values:**
   ```
   Host: aws-0-us-east-1.pooler.supabase.com
   Port: 6543
   Database: postgres
   User: postgres.abcdefghij
   Password: [the password you created in step 2]
   ```

### Step 2: Enable pgvector Extension

1. In Supabase dashboard, go to **SQL Editor** (left sidebar)
2. Click **New Query**
3. Paste this command:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Click **RUN** (or press Ctrl+Enter)
5. You should see "Success. No rows returned"

### Step 3: Update Your .env File

Open your `.env` file and update these variables:

**BEFORE (Local PostgreSQL):**
```env
DB_HOST=localhost
DB_NAME=mba_data
DB_USER=postgres
DB_PASSWORD=your_local_password
DB_PORT=5432
```

**AFTER (Supabase):**
```env
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_NAME=postgres
DB_USER=postgres.abcdefghij
DB_PASSWORD=your_supabase_password
DB_PORT=6543
```

**Important Notes:**
- Replace `aws-0-us-east-1.pooler.supabase.com` with YOUR actual Supabase host
- Replace `postgres.abcdefghij` with YOUR actual Supabase user
- Replace `your_supabase_password` with the password you created
- Port `6543` is for **connection pooling** (recommended for production)
- Port `5432` is for **direct connection** (only use for debugging)

### Step 4: Run the Migration Script

Now migrate your existing data from local PostgreSQL to Supabase:

```bash
python migrate_to_supabase.py
```

**What this script does:**
1. Asks for your **local database** credentials
2. Asks for your **Supabase** credentials (or reads from .env)
3. Exports all data from local database
4. Imports all data to Supabase
5. Shows progress for each table

**Example interaction:**
```
Local database name (default: mba_data): [press Enter]
Local database user (default: postgres): [press Enter]
Local database password: your_local_password

Supabase host: aws-0-us-east-1.pooler.supabase.com
Supabase user: postgres.abcdefghij
Supabase password: your_supabase_password
Supabase port (6543 for pooling, 5432 for direct): 6543

Continue with migration? [y/N]: y
```

### Step 5: Verify the Migration

Run the validation script to ensure everything migrated correctly:

```bash
python validate_setup.py
```

This will check:
- ✅ Database connection
- ✅ All tables exist
- ✅ Data was migrated
- ✅ Row counts match

### Step 6: Test the Application

Start your application with the new Supabase database:

```bash
python app.py
```

Open your browser and test all features to ensure everything works!

---

## 🔄 Alternative: Fresh Start (No Migration)

If you don't have important data in local database, or want to start fresh:

### Option 1: Just Run the Scrapers

```bash
# Update .env with Supabase credentials (Step 3 above)

# Verify Supabase connection
python setup_supabase.py

# Populate with fresh data
python scraper.py
python reviews_scraper.py

# Start app
python app.py
```

### Option 2: Full Setup for Supabase

```bash
# Update .env with Supabase credentials

# Run setup (creates tables automatically)
python setup.py

# Populate data
python scraper.py
python reviews_scraper.py

# Start app
python app.py
```

---

## 📋 Environment Variables Summary

### Complete .env File for Supabase

```env
# ============================================
# SUPABASE DATABASE CONFIGURATION
# ============================================
# Get these from: Supabase Dashboard → Settings → Database

DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_NAME=postgres
DB_USER=postgres.abcdefghij
DB_PASSWORD=your_supabase_password_here
DB_PORT=6543

# Notes:
# - Host: From "Connection pooling" section
# - User: Starts with "postgres." followed by random characters
# - Password: The one you set when creating the project
# - Port 6543: Connection pooling (recommended)
# - Port 5432: Direct connection (only for debugging)

# ============================================
# APPLICATION SETTINGS
# ============================================
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your_random_secret_key_here

# ============================================
# OPTIONAL API KEYS
# ============================================
AZURE_OPENAI_API_KEY=your_openai_api_key_here
UNSTRUCTURED_API_KEY=your_unstructured_api_key_here

# Optional: Supabase API (for future features)
# SUPABASE_URL=https://abcdefghij.supabase.co
# SUPABASE_ANON_KEY=your_anon_key_here
```

---

## 🛠️ Troubleshooting

### Issue: "Connection timeout"
**Solution:** Check your internet connection and verify Supabase project is active

### Issue: "SSL required"
**Solution:** The scripts automatically handle this - no action needed!

### Issue: "Authentication failed"
**Solution:** 
- Double-check your password (copy-paste from Supabase dashboard)
- Ensure user includes the full `postgres.xxxxx` format

### Issue: "Database does not exist"
**Solution:** 
- Supabase always uses database name `postgres`, not `mba_data`
- Make sure `.env` has `DB_NAME=postgres`

### Issue: "Too many connections"
**Solution:** 
- Use connection pooling port `6543`
- Free tier allows 15 concurrent connections

---

## 📊 Quick Comparison

| What | Local PostgreSQL | Supabase |
|------|------------------|----------|
| **DB_HOST** | localhost | aws-0-region.pooler.supabase.com |
| **DB_NAME** | mba_data | postgres |
| **DB_USER** | postgres | postgres.xxxxxxxxxxxxx |
| **DB_PORT** | 5432 | 6543 (pooling) or 5432 (direct) |
| **SSL** | Optional | Required (auto-handled) |

---

## ✅ Verification Checklist

After migration, verify these items:

- [ ] `.env` file updated with Supabase credentials
- [ ] `python setup_supabase.py` runs successfully
- [ ] `python validate_setup.py` shows all tables present
- [ ] Can see data in Supabase Dashboard → Table Editor
- [ ] `python app.py` starts without errors
- [ ] Can interact with chatbot in browser
- [ ] University cards display correctly

---

## 🎯 Summary

**3 Simple Steps:**

1. **Create Supabase project** → Get connection details
2. **Update `.env` file** → Replace 5 variables
3. **Run migration** → `python migrate_to_supabase.py`

**That's it!** Your MBA Bot is now running on Supabase! 🎉

---

## 💡 Pro Tips

1. **Save your Supabase password** - Store it in a password manager
2. **Bookmark Supabase dashboard** - You'll use it to monitor your database
3. **Check storage usage** - Free tier has 500MB limit
4. **Use connection pooling** - Port 6543 is recommended for production
5. **Enable backups** - Supabase auto-backs up daily (free tier keeps 7 days)

For more details, see:
- **Full Guide**: `supabase_setup.md`
- **Technical Info**: `SUPABASE_MIGRATION.md`
