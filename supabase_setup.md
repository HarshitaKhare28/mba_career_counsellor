# Supabase Migration Guide

## Overview
This guide will help you migrate your MBA Bot database from local PostgreSQL to Supabase, a managed PostgreSQL service with built-in pgvector support.

## Why Supabase?

- ✅ **Managed PostgreSQL**: No need to install PostgreSQL locally
- ✅ **Built-in pgvector**: Vector similarity search out of the box
- ✅ **Free tier**: Generous free tier for development and small projects
- ✅ **Automatic backups**: Your data is safe and backed up
- ✅ **Scalable**: Easy to scale as your application grows
- ✅ **Global CDN**: Fast access from anywhere

## Step-by-Step Migration

### 1. Create a Supabase Account

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign up with GitHub, Google, or email
4. Create a new organization (if needed)

### 2. Create a New Project

1. Click "New Project"
2. Fill in the details:
   - **Name**: `mba-career-counselor` (or your preferred name)
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose the closest region to your users
   - **Pricing Plan**: Free tier is sufficient for development
3. Click "Create new project"
4. Wait 2-3 minutes for project provisioning

### 3. Get Your Database Credentials

Once your project is ready:

1. Go to **Project Settings** (gear icon in sidebar)
2. Navigate to **Database** section
3. Scroll down to **Connection string**
4. Copy the **Connection pooling** string (recommended for production)
   - Example: `postgresql://postgres.xxxxx:password@aws-0-region.pooler.supabase.com:6543/postgres`

**Important Connection Details:**
```
Host: aws-0-[region].pooler.supabase.com
Port: 6543 (pooler) or 5432 (direct)
Database: postgres
User: postgres.xxxxx
Password: [your-password]
```

### 4. Enable pgvector Extension

Supabase has pgvector pre-installed, but you need to enable it:

1. Go to **SQL Editor** in Supabase dashboard
2. Click **New Query**
3. Run this SQL command:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Click **RUN** or press `Ctrl+Enter`
5. You should see "Success. No rows returned"

### 5. Update Your .env File

Update your `.env` file with Supabase credentials:

```env
# Supabase Database Configuration
DB_HOST=aws-0-us-east-1.pooler.supabase.com  # Your Supabase host
DB_NAME=postgres
DB_USER=postgres.abcdefghijklmnop  # Your Supabase user
DB_PASSWORD=your_supabase_password_here
DB_PORT=6543  # Use 6543 for connection pooling (recommended)

# Alternative: Direct Connection (not recommended for production)
# DB_HOST=db.abcdefghijklmnop.supabase.co
# DB_PORT=5432

# Application Settings
FLASK_ENV=production  # Change to production for Supabase
FLASK_DEBUG=false
```

### 6. Run the Migration

Now run the setup scripts to create tables and populate data:

```bash
# Test database connection
python test_database.py

# Run schema update (creates all tables)
python update_schema.py

# Process and upload data
python scraper.py

# Add reviews and alumni status
python reviews_scraper.py

# Validate everything is working
python validate_setup.py
```

### 7. Verify in Supabase Dashboard

1. Go to **Table Editor** in Supabase
2. You should see three tables:
   - `universities`
   - `mba_embeddings`
   - `conversations`
3. Click on each table to verify data is there
4. Check the **Database** section to see storage usage

## Connection Types

### Connection Pooling (Recommended)
- **Port**: 6543
- **Best for**: Production applications
- **Max connections**: 15 (free tier)
- **Use when**: Deploying to production or serverless

### Direct Connection
- **Port**: 5432
- **Best for**: Development and testing
- **Max connections**: Unlimited
- **Use when**: Running locally or debugging

## Environment Variables Template

Create or update your `.env` file:

```env
# Supabase PostgreSQL Database
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_NAME=postgres
DB_USER=postgres.xxxxxxxxxxxxx
DB_PASSWORD=your_strong_password_here
DB_PORT=6543

# Application Configuration
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your_secret_key_here

# Optional: Supabase API (for future features)
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=your_anon_key_here
```

## Security Best Practices

### 1. Enable Row Level Security (RLS)
Supabase recommends enabling RLS for production:

```sql
-- Enable RLS on universities table
ALTER TABLE universities ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public read access
CREATE POLICY "Allow public read access" ON universities
FOR SELECT USING (true);

-- Repeat for other tables as needed
```

### 2. Use Environment Variables
- ✅ Never commit `.env` file to Git
- ✅ Use different databases for development/production
- ✅ Rotate passwords regularly

### 3. Connection Limits
Free tier limits:
- **Connection pooling**: 15 concurrent connections
- **Direct connections**: Unlimited but not recommended

## Troubleshooting

### Connection Timeout
**Error**: `could not connect to server: Connection timed out`

**Solutions**:
1. Check if your IP is whitelisted (Supabase allows all by default)
2. Verify the connection string is correct
3. Try using direct connection (port 5432) instead of pooling

### SSL Certificate Error
**Error**: `SSL connection required`

**Solution**: Add SSL mode to connection:
```python
db_config = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': int(os.getenv('DB_PORT', '6543')),
    'sslmode': 'require'  # Add this line
}
```

### Too Many Connections
**Error**: `FATAL: remaining connection slots are reserved`

**Solutions**:
1. Use connection pooling (port 6543)
2. Close connections properly in your code
3. Upgrade to paid tier for more connections

### pgvector Not Found
**Error**: `extension "vector" does not exist`

**Solution**: Run in Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Monitoring and Maintenance

### Database Dashboard
Monitor your database in Supabase:
- **Database Size**: Settings → Database → Database size
- **Active Connections**: Database → Connection pooling
- **Query Performance**: Database → Query performance

### Backup Strategy
Supabase automatically backs up your database:
- **Daily backups**: Retained for 7 days (free tier)
- **Point-in-time recovery**: Available on paid plans

### Scaling Up
When you need more resources:
1. Go to **Settings → Billing**
2. Choose a paid plan:
   - **Pro**: $25/month - 500GB storage, unlimited connections
   - **Team**: Custom pricing for larger needs

## Migration from Local to Supabase

If you have existing data in local PostgreSQL:

### Option 1: Dump and Restore
```bash
# Export from local PostgreSQL
pg_dump -h localhost -U postgres mba_data > local_backup.sql

# Import to Supabase (update connection details)
psql "postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres" < local_backup.sql
```

### Option 2: Use Python Scripts (Recommended)
Just run the scraper scripts again - they will populate Supabase with fresh data:
```bash
python scraper.py
python reviews_scraper.py
```

## Cost Estimation

### Free Tier (Perfect for Development)
- ✅ 500 MB database space
- ✅ 1 GB file storage
- ✅ 2 GB bandwidth
- ✅ 50 MB file upload
- ✅ Unlimited API requests
- ✅ Up to 500 MB of pgvector indexes

### When to Upgrade
Consider upgrading when:
- Database size > 500 MB
- Need > 15 concurrent connections
- Require point-in-time recovery
- Need dedicated resources

## Next Steps

After migration:
1. ✅ Test all functionality with `python validate_setup.py`
2. ✅ Update deployment configurations
3. ✅ Set up monitoring and alerts
4. ✅ Configure backups strategy
5. ✅ Deploy your Flask app to production

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [pgvector on Supabase](https://supabase.com/docs/guides/ai/vector-columns)
- [Connection Pooling Guide](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)

---

**🎉 Congratulations!** You've successfully migrated to Supabase. Your MBA Bot now runs on a scalable, managed database platform!
