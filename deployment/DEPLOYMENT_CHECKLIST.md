# 🎯 Azure Deployment Checklist

Track your progress deploying MBABOT to Azure with Supabase.

---

## Phase 1: Environment Setup ⚙️

- [ ] Python 3.12 installed
- [ ] pip updated (`python -m pip install --upgrade pip`)
- [ ] Azure CLI installed
- [ ] Git installed (for version control)

---

## Phase 2: Supabase Configuration ☁️

- [ ] Created Supabase account at https://supabase.com
- [ ] Created new Supabase project
- [ ] Noted project region: _______________
- [ ] Copied database password (save securely!)
- [ ] Retrieved connection string from Dashboard → Settings → Database

### Connection Details Collected:
- [ ] `DB_HOST`: db.xxxxxxxxxxxxx.supabase.co
- [ ] `DB_NAME`: postgres (default)
- [ ] `DB_USER`: postgres.xxxxxxxxxxxxx
- [ ] `DB_PASSWORD`: _______________
- [ ] `DB_PORT`: 6543 (pooler)

---

## Phase 3: Local .env Configuration 📝

- [ ] Created `.env` file in project root
- [ ] Added all Supabase credentials
- [ ] Verified `.env` is in `.gitignore`
- [ ] Double-checked no typos in credentials

**Test Command**:
```bash
python setup_supabase.py
```

**Expected Output**: ✅ All green checkmarks

---

## Phase 4: Database Setup 🗄️

Run the full setup script:
```bash
python full_setup.py
```

- [ ] Selected Option 2 (Supabase)
- [ ] Supabase connection verified
- [ ] Database schema created successfully
- [ ] pgvector extension enabled
- [ ] Universities table populated (20 universities)
- [ ] Reviews data integrated
- [ ] Embeddings generated
- [ ] Sample queries tested

**Verification**: Run `python validate_setup.py`
- [ ] All validation checks passed

---

## Phase 5: Azure Account Setup 🔐

- [ ] Created Azure account (or logged in)
- [ ] Activated free tier credits (if available)
- [ ] Installed Azure CLI
- [ ] Logged in: `az login`
- [ ] Selected subscription: `az account set --subscription "Your Subscription"`

---

## Phase 6: Azure Resource Creation 🏗️

### Resource Group
```bash
az group create --name mbabot-rg --location eastus
```
- [ ] Resource group created
- [ ] Confirmed in Azure Portal

### App Service Plan
```bash
az appservice plan create --name mbabot-plan --resource-group mbabot-rg --sku F1 --is-linux
```
- [ ] App Service Plan created (Free tier F1)
- [ ] Plan type: Linux confirmed

### Web App
```bash
az webapp create --resource-group mbabot-rg --plan mbabot-plan --name mbabot-app --runtime "PYTHON:3.12"
```
- [ ] Web App created
- [ ] App name: _______________
- [ ] URL: https://_______________.azurewebsites.net

---

## Phase 7: Environment Variables Configuration 🔧

Configure in Azure Portal or via CLI:

```bash
az webapp config appsettings set --resource-group mbabot-rg --name mbabot-app --settings \
    DB_HOST="your_supabase_host" \
    DB_NAME="postgres" \
    DB_USER="your_supabase_user" \
    DB_PASSWORD="your_password" \
    DB_PORT="6543"
```

- [ ] All environment variables set
- [ ] Verified in Azure Portal → Configuration → Application settings

**Variables Checklist**:
- [ ] DB_HOST
- [ ] DB_NAME
- [ ] DB_USER
- [ ] DB_PASSWORD
- [ ] DB_PORT

---

## Phase 8: Deployment Files ✅

Verify these files exist in project root:

- [ ] `startup.sh` - Created by full_setup.py
- [ ] `.deployment` - Created by full_setup.py
- [ ] `runtime.txt` - Created by full_setup.py
- [ ] `requirements.txt` - Contains gunicorn==23.0.0
- [ ] `app.py` - Flask application entry point

---

## Phase 9: Deploy Application 🚀

### Option A: Azure CLI Deployment
```bash
az webapp up --resource-group mbabot-rg --name mbabot-app --runtime "PYTHON:3.12"
```

### Option B: Git Deployment
```bash
git init
git add .
git commit -m "Initial deployment"
az webapp deployment source config-local-git --name mbabot-app --resource-group mbabot-rg
git remote add azure <deployment-url>
git push azure main
```

- [ ] Deployment initiated
- [ ] Build completed successfully
- [ ] Application started

---

## Phase 10: Verification & Testing 🧪

- [ ] Application URL accessible: https://_______________.azurewebsites.net
- [ ] Homepage loads correctly
- [ ] Chatbot interface visible
- [ ] Test query: "I want an MBA with good ROI"
- [ ] Chatbot responds with university recommendations
- [ ] No errors in browser console

### Check Azure Logs
```bash
az webapp log tail --resource-group mbabot-rg --name mbabot-app
```
- [ ] Logs streaming successfully
- [ ] No critical errors
- [ ] Gunicorn workers started

---

## Phase 11: Post-Deployment Configuration 🔧

### Enable Logging
```bash
az webapp log config --name mbabot-app --resource-group mbabot-rg \
    --application-logging filesystem \
    --level information
```
- [ ] Application logging enabled
- [ ] Log level set to Information

### Set Up Health Check (Optional)
```bash
az webapp config set --resource-group mbabot-rg --name mbabot-app \
    --health-check-path "/"
```
- [ ] Health check configured

### Enable HTTPS Only
```bash
az webapp update --resource-group mbabot-rg --name mbabot-app --https-only true
```
- [ ] HTTPS enforced

---

## Phase 12: Monitoring Setup 📊

- [ ] Opened Azure Portal → Your Web App
- [ ] Checked Metrics dashboard
- [ ] Set up alert for HTTP 5xx errors
- [ ] Set up alert for high CPU usage (>80%)
- [ ] Enabled Application Insights (optional)

---

## Phase 13: Database Monitoring 🗄️

### Supabase Dashboard
- [ ] Checked database size (Free tier: <500MB)
- [ ] Verified tables exist: universities, mba_embeddings, conversations
- [ ] Checked API usage
- [ ] Reviewed connection pooling stats

### Test Queries in Supabase
```sql
SELECT COUNT(*) FROM universities;  -- Should be 20
SELECT COUNT(*) FROM mba_embeddings;  -- Should be 20
SELECT name, review_rating, review_count FROM universities WHERE review_rating IS NOT NULL;
```
- [ ] All queries return expected results

---

## Phase 14: Performance Testing 🚀

- [ ] Tested chatbot response time (<3 seconds)
- [ ] Tested with multiple queries in sequence
- [ ] Tested edge cases (empty query, very long query)
- [ ] Verified database connection pooling working
- [ ] No memory leaks after 10+ queries

---

## Phase 15: Security Review 🔐

- [ ] `.env` file NOT committed to git
- [ ] `.env` in `.gitignore`
- [ ] Azure environment variables secured
- [ ] Supabase password changed from default
- [ ] HTTPS enforced on Azure Web App
- [ ] No sensitive data in logs
- [ ] Database uses SSL connection (automatic with Supabase)

---

## Phase 16: Documentation 📚

- [ ] Updated README.md with deployment URL
- [ ] Documented any custom configurations
- [ ] Created runbook for common issues
- [ ] Shared access with team (if applicable)

---

## Phase 17: Scaling Preparation 📈

### When to Upgrade:

**From Free (F1) to Basic (B1)**:
- [ ] CPU usage consistently >80%
- [ ] Need custom domain
- [ ] Need auto-scaling
- [ ] >60 minutes CPU/day usage

**From Supabase Free to Pro**:
- [ ] Database size >400MB
- [ ] >1GB bandwidth/month
- [ ] Need daily backups
- [ ] Need better performance

### Upgrade Commands (When Ready):
```bash
# Upgrade App Service Plan
az appservice plan update --name mbabot-plan --resource-group mbabot-rg --sku B1

# For production with auto-scale
az appservice plan update --name mbabot-plan --resource-group mbabot-rg --sku P1V2
```

---

## 🎉 Deployment Complete!

### Final Verification Checklist:

- [ ] ✅ Application live at: https://_______________.azurewebsites.net
- [ ] ✅ Chatbot responding to queries
- [ ] ✅ Database connected via Supabase
- [ ] ✅ No errors in Azure logs
- [ ] ✅ HTTPS working
- [ ] ✅ Monitoring enabled
- [ ] ✅ All environment variables configured
- [ ] ✅ Free tier limits understood

---

## 📝 Important Information

**Save These Details**:
- Azure Resource Group: mbabot-rg
- App Service Plan: mbabot-plan
- Web App Name: _______________
- App URL: _______________
- Supabase Project: _______________
- Deployment Date: _______________

**Monthly Costs** (Initial):
- Azure Free Tier: $0 (60 CPU minutes/day limit)
- Supabase Free: $0 (<500MB, <2GB bandwidth)
- **Total**: $0/month 🎉

**When to Budget for Scaling**:
- Azure Basic (B1): ~$13/month
- Supabase Pro: $25/month
- **Total Production**: ~$38/month

---

## 🆘 Troubleshooting

### Issue: Application Not Starting
- [ ] Check Azure logs: `az webapp log tail`
- [ ] Verify `startup.sh` has execute permissions
- [ ] Check `requirements.txt` includes all dependencies
- [ ] Verify Python version matches (3.12)

### Issue: Database Connection Failed
- [ ] Run `python setup_supabase.py` locally
- [ ] Verify environment variables in Azure Portal
- [ ] Check Supabase project is active
- [ ] Verify SSL is enabled (automatic)

### Issue: 500 Internal Server Error
- [ ] Check application logs
- [ ] Verify all environment variables set
- [ ] Test locally first: `python app.py`
- [ ] Check for missing dependencies

### Issue: Slow Response Times
- [ ] Check Supabase connection pooling (port 6543)
- [ ] Review database query performance
- [ ] Consider upgrading App Service Plan
- [ ] Enable Application Insights for profiling

---

## 🎓 Learning Resources

- Azure App Service: https://docs.microsoft.com/azure/app-service/
- Supabase Docs: https://supabase.com/docs
- Flask Deployment: https://flask.palletsprojects.com/deployment/
- pgvector Guide: https://github.com/pgvector/pgvector

---

**Last Updated**: _______________
**Deployment Status**: ⏳ In Progress / ✅ Complete
**Notes**: _______________________________________________

---

## Next Steps After Completion

1. **Share with stakeholders**
2. **Set up CI/CD pipeline** (GitHub Actions)
3. **Configure custom domain** (optional)
4. **Enable Application Insights** for detailed analytics
5. **Plan scaling strategy** based on usage patterns

---

Good luck with your deployment! 🚀✨
