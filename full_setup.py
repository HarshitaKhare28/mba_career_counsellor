#!/usr/bin/env python3
"""
Full Setup Script for MBA Bot
Supports both Local PostgreSQL and Supabase deployment
Includes Azure deployment preparation
"""
import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

def print_banner(text):
    """Print a formatted banner"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_section(text):
    """Print a section header"""
    print(f"\n{'─' * 70}")
    print(f"📌 {text}")
    print(f"{'─' * 70}")

def run_script(script_name, description, skip_on_error=False):
    """Run a Python script and return success status"""
    print(f"\n🔄 {description}...")
    print("-" * 50)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, text=True, check=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with error code {e.returncode}")
        if skip_on_error:
            print("⚠️ Continuing anyway (this step is optional)...")
            return True
        return False
    except FileNotFoundError:
        print(f"❌ Script {script_name} not found!")
        if skip_on_error:
            print("⚠️ Continuing anyway (this step is optional)...")
            return True
        return False

def choose_deployment_type():
    """Let user choose between local PostgreSQL and Supabase"""
    print_section("Database Selection")
    print("\nChoose your database deployment:")
    print("  1. 🐘 Local PostgreSQL (Self-hosted, for development)")
    print("  2. ☁️  Supabase (Cloud PostgreSQL, recommended for production)")
    print("  3. 📋 Show comparison and help me decide")
    print()
    
    while True:
        choice = input("Enter your choice [1/2/3]: ").strip()
        
        if choice == "3":
            show_database_comparison()
            continue
        elif choice in ["1", "2"]:
            return choice
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

def show_database_comparison():
    """Show comparison between Local PostgreSQL and Supabase"""
    print("\n" + "=" * 70)
    print("  📊 Database Comparison")
    print("=" * 70)
    print("\n┌─────────────────────┬──────────────────────┬──────────────────────┐")
    print("│ Feature             │ Local PostgreSQL     │ Supabase            │")
    print("├─────────────────────┼──────────────────────┼──────────────────────┤")
    print("│ Setup Time          │ 30+ minutes          │ 5 minutes           │")
    print("│ Installation        │ Required             │ None                │")
    print("│ Cost                │ Free (self-hosted)   │ Free tier (500MB)   │")
    print("│ Maintenance         │ Self-managed         │ Fully managed       │")
    print("│ Backups             │ Manual               │ Automatic           │")
    print("│ Scalability         │ Manual               │ Easy                │")
    print("│ Remote Access       │ Needs config         │ Built-in            │")
    print("│ Azure Deployment    │ Complex              │ Simple              │")
    print("│ Best For            │ Local dev/testing    │ Production/Azure    │")
    print("└─────────────────────┴──────────────────────┴──────────────────────┘")
    print("\n💡 Recommendation:")
    print("   • Development/Testing: Local PostgreSQL")
    print("   • Production/Azure: Supabase (much easier!)")
    print()

def check_env_file():
    """Check if .env file exists and is configured"""
    if not os.path.exists('.env'):
        print("⚠️ .env file not found!")
        return False
    
    load_dotenv()
    
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def setup_local_postgresql():
    """Setup with local PostgreSQL"""
    print_section("Local PostgreSQL Setup")
    
    scripts = [
        ("setup.py", "Environment and dependency setup", False),
        ("test_database.py", "Database creation and connection test", False),
        ("update_schema.py", "Database schema update", False),
        ("scraper.py", "Data processing and embeddings creation", False),
        ("reviews_scraper.py", "Reviews scraping and alumni status update", True),
        ("validate_setup.py", "Setup validation", True)
    ]
    
    success_count = 0
    
    for script, description, skip_on_error in scripts:
        if run_script(script, description, skip_on_error):
            success_count += 1
        else:
            if not skip_on_error:
                print(f"\n💥 Setup failed at: {description}")
                print("Please check the error messages above and resolve issues.")
                return False
    
    return success_count > 0

def setup_supabase():
    """Setup with Supabase"""
    print_section("Supabase Setup")
    
    # Check if .env is configured for Supabase
    if not check_env_file():
        print("\n📝 Supabase Configuration Required")
        print("\nPlease follow these steps:")
        print("  1. Create a Supabase account at https://supabase.com")
        print("  2. Create a new project")
        print("  3. Get your connection details from Settings → Database")
        print("  4. Update your .env file with:")
        print()
        print("     DB_HOST=aws-0-region.pooler.supabase.com")
        print("     DB_NAME=postgres")
        print("     DB_USER=postgres.xxxxxxxxxxxxx")
        print("     DB_PASSWORD=your_supabase_password")
        print("     DB_PORT=6543")
        print()
        print("📖 See MIGRATION_QUICKSTART.md for detailed instructions")
        print()
        
        response = input("Have you configured your .env file? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Please configure .env file first, then re-run this script.")
            return False
    
    scripts = [
        ("setup.py", "Environment and dependency setup", False),
        ("setup_supabase.py", "Supabase connection verification", False),
        ("update_schema.py", "Database schema setup", False),
        ("scraper.py", "Data processing and embeddings creation", False),
        ("reviews_scraper.py", "Reviews scraping and alumni status update", True),
        ("validate_setup.py", "Setup validation", True)
    ]
    
    success_count = 0
    
    for script, description, skip_on_error in scripts:
        if run_script(script, description, skip_on_error):
            success_count += 1
        else:
            if not skip_on_error:
                print(f"\n💥 Setup failed at: {description}")
                print("Please check the error messages above and resolve issues.")
                return False
    
    return success_count > 0

def prepare_for_azure():
    """Prepare application for Azure deployment"""
    print_section("Azure Deployment Preparation")
    
    print("\n📦 Creating Azure deployment files...")
    
    # Create requirements.txt if not exists
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found!")
        return False
    print("✅ requirements.txt found")
    
    # Create runtime.txt for Python version
    runtime_file = Path('runtime.txt')
    if not runtime_file.exists():
        python_version = f"python-{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        runtime_file.write_text(python_version)
        print(f"✅ Created runtime.txt with {python_version}")
    else:
        print("✅ runtime.txt already exists")
    
    # Create startup command file for Azure
    startup_file = Path('startup.sh')
    startup_content = """#!/bin/bash
# Azure Web App startup script for MBA Bot

echo "Starting MBA Career Counselor Bot..."

# Install dependencies
pip install -r requirements.txt

# Run database migrations if needed
python update_schema.py || echo "Schema already up to date"

# Start the Flask application
gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app
"""
    if not startup_file.exists():
        startup_file.write_text(startup_content)
        print("✅ Created startup.sh for Azure")
    else:
        print("✅ startup.sh already exists")
    
    # Create .deployment file
    deployment_file = Path('.deployment')
    deployment_content = """[config]
command = bash startup.sh
"""
    if not deployment_file.exists():
        deployment_file.write_text(deployment_content)
        print("✅ Created .deployment file")
    else:
        print("✅ .deployment file already exists")
    
    # Create Azure-specific requirements
    azure_requirements = ['gunicorn>=20.1.0']
    current_requirements = Path('requirements.txt').read_text()
    
    if 'gunicorn' not in current_requirements:
        with open('requirements.txt', 'a') as f:
            f.write('\n# Azure deployment\n')
            f.write('gunicorn>=20.1.0\n')
        print("✅ Added gunicorn to requirements.txt")
    else:
        print("✅ gunicorn already in requirements.txt")
    
    # Create Azure deployment guide
    azure_guide = Path('AZURE_DEPLOYMENT.md')
    if not azure_guide.exists():
        create_azure_deployment_guide()
        print("✅ Created AZURE_DEPLOYMENT.md")
    else:
        print("✅ AZURE_DEPLOYMENT.md already exists")
    
    print("\n✅ Azure deployment preparation complete!")
    return True

def create_azure_deployment_guide():
    """Create Azure deployment guide"""
    content = """# Azure Deployment Guide for MBA Bot

## Prerequisites
- Azure account (free tier available)
- Supabase database configured
- Application tested locally

## Deployment Options

### Option 1: Azure Web App (Recommended)

#### 1. Create Azure Web App
```bash
# Install Azure CLI
# Windows: https://aka.ms/installazurecliwindows
# Mac: brew install azure-cli
# Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Create resource group
az group create --name mba-bot-rg --location eastus

# Create App Service plan (Free tier)
az appservice plan create --name mba-bot-plan --resource-group mba-bot-rg --sku F1 --is-linux

# Create Web App
az webapp create --resource-group mba-bot-rg --plan mba-bot-plan --name mba-career-counselor --runtime "PYTHON:3.11"
```

#### 2. Configure Environment Variables
```bash
# Set database credentials
az webapp config appsettings set --resource-group mba-bot-rg --name mba-career-counselor --settings \\
    DB_HOST="your-supabase-host" \\
    DB_NAME="postgres" \\
    DB_USER="your-supabase-user" \\
    DB_PASSWORD="your-supabase-password" \\
    DB_PORT="6543" \\
    FLASK_ENV="production" \\
    FLASK_DEBUG="false"
```

#### 3. Deploy Application
```bash
# Deploy from local directory
az webapp up --resource-group mba-bot-rg --name mba-career-counselor --runtime "PYTHON:3.11"

# Or deploy from GitHub
az webapp deployment source config --name mba-career-counselor --resource-group mba-bot-rg \\
    --repo-url https://github.com/Ankit0431/MBA_Career_Counceller --branch main --manual-integration
```

#### 4. View Application
```bash
# Open in browser
az webapp browse --name mba-career-counselor --resource-group mba-bot-rg

# View logs
az webapp log tail --name mba-career-counselor --resource-group mba-bot-rg
```

### Option 2: Azure Container Instances

#### 1. Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "600", "app:app"]
```

#### 2. Build and Deploy
```bash
# Build container
docker build -t mba-bot .

# Create Azure Container Registry
az acr create --resource-group mba-bot-rg --name mbabotregistry --sku Basic

# Push to ACR
az acr login --name mbabotregistry
docker tag mba-bot mbabotregistry.azurecr.io/mba-bot:v1
docker push mbabotregistry.azurecr.io/mba-bot:v1

# Deploy to Container Instances
az container create --resource-group mba-bot-rg --name mba-bot-container \\
    --image mbabotregistry.azurecr.io/mba-bot:v1 \\
    --dns-name-label mba-career-counselor \\
    --ports 8000
```

## Environment Variables for Azure

Set these in Azure Web App → Configuration → Application Settings:

```
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_NAME=postgres
DB_USER=postgres.xxxxxxxxxxxxx
DB_PASSWORD=your_supabase_password
DB_PORT=6543
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your_random_secret_key
```

## Cost Estimation

### Free Tier (F1)
- ✅ $0/month
- 1 GB RAM
- 1 GB storage
- Good for development/testing

### Basic Tier (B1)
- ~$13/month
- 1.75 GB RAM
- 10 GB storage
- Good for small production

### Standard Tier (S1)
- ~$70/month
- 1.75 GB RAM
- 50 GB storage
- Auto-scaling, custom domains

## Troubleshooting

### Application won't start
- Check logs: `az webapp log tail --name mba-career-counselor --resource-group mba-bot-rg`
- Verify environment variables are set
- Check Supabase connection

### Database connection fails
- Verify Supabase credentials
- Check network connectivity
- Ensure port 6543 is allowed

### Static files not loading
- Check app.py configuration
- Verify static folder path
- Check Azure storage configuration

## Monitoring

### View Logs
```bash
# Stream logs
az webapp log tail --name mba-career-counselor --resource-group mba-bot-rg

# Download logs
az webapp log download --name mba-career-counselor --resource-group mba-bot-rg
```

### Set up Application Insights
```bash
az monitor app-insights component create --app mba-bot-insights \\
    --location eastus --resource-group mba-bot-rg \\
    --application-type web

# Link to Web App
az webapp config appsettings set --resource-group mba-bot-rg --name mba-career-counselor \\
    --settings APPINSIGHTS_INSTRUMENTATIONKEY="your-key"
```

## Scaling

### Manual Scaling
```bash
# Scale up (change instance size)
az appservice plan update --name mba-bot-plan --resource-group mba-bot-rg --sku B2

# Scale out (more instances)
az webapp scale --name mba-career-counselor --resource-group mba-bot-rg --instance-count 2
```

### Auto-scaling (Standard tier and above)
```bash
# Enable auto-scale
az monitor autoscale create --resource-group mba-bot-rg --name mba-bot-autoscale \\
    --resource mba-career-counselor --resource-type Microsoft.Web/sites \\
    --min-count 1 --max-count 3 --count 1
```

## Security Best Practices

1. **Use Managed Identity** for Azure services
2. **Enable HTTPS only** in Web App settings
3. **Set up IP restrictions** if needed
4. **Use Azure Key Vault** for secrets
5. **Enable authentication** (Azure AD, Google, etc.)

## Useful Commands

```bash
# Restart app
az webapp restart --name mba-career-counselor --resource-group mba-bot-rg

# Stop app
az webapp stop --name mba-career-counselor --resource-group mba-bot-rg

# Start app
az webapp start --name mba-career-counselor --resource-group mba-bot-rg

# Delete app
az webapp delete --name mba-career-counselor --resource-group mba-bot-rg

# Delete resource group (deletes everything)
az group delete --name mba-bot-rg --yes
```

## Next Steps

1. Set up custom domain
2. Configure SSL certificate
3. Set up CI/CD with GitHub Actions
4. Configure monitoring and alerts
5. Set up backup strategy

---

**🎉 Your MBA Bot is now deployed on Azure!**
"""
    Path('AZURE_DEPLOYMENT.md').write_text(content)

def show_completion_summary(deployment_type, success):
    """Show completion summary and next steps"""
    print_banner("Setup Summary")
    
    if success:
        print("\n✅ Setup completed successfully!")
        
        if deployment_type == "1":
            print("\n📋 Local PostgreSQL Setup Complete")
            print("\nNext steps:")
            print("  1. Run: python app.py")
            print("  2. Open browser: http://localhost:5000")
            print("  3. Test the chatbot functionality")
            
        elif deployment_type == "2":
            print("\n📋 Supabase Setup Complete")
            print("\nNext steps for local testing:")
            print("  1. Run: python app.py")
            print("  2. Open browser: http://localhost:5000")
            print("  3. Test the chatbot functionality")
            print("\n☁️ Ready for Azure deployment!")
            print("  • All files prepared for Azure")
            print("  • See AZURE_DEPLOYMENT.md for deployment steps")
            print("  • Database: Already on Supabase (cloud-ready)")
    else:
        print("\n❌ Setup incomplete")
        print("\nPlease resolve the errors above and re-run:")
        print("  python full_setup.py")
    
    print(f"\n📁 Working directory: {os.getcwd()}")

def main():
    """Main setup orchestrator"""
    print_banner("MBA Career Counselor - Full Setup")
    
    print("\n🎯 This setup wizard will:")
    print("  ✓ Install all dependencies")
    print("  ✓ Configure your database (Local or Supabase)")
    print("  ✓ Create database schema")
    print("  ✓ Process and import MBA data")
    print("  ✓ Add reviews and alumni information")
    print("  ✓ Prepare for Azure deployment (optional)")
    
    # Ask user to continue
    print()
    response = input("Continue with setup? [Y/n]: ").strip().lower()
    if response and response not in ['y', 'yes']:
        print("Setup cancelled by user.")
        return
    
    # Choose deployment type
    deployment_type = choose_deployment_type()
    
    success = False
    
    if deployment_type == "1":
        # Local PostgreSQL setup
        success = setup_local_postgresql()
    else:
        # Supabase setup
        success = setup_supabase()
        
        if success:
            # Prepare for Azure deployment
            print()
            response = input("\n🌐 Prepare for Azure deployment? [Y/n]: ").strip().lower()
            if not response or response in ['y', 'yes']:
                prepare_for_azure()
    
    # Show completion summary
    show_completion_summary(deployment_type, success)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)