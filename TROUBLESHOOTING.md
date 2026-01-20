# APIC Troubleshooting Guide

This guide helps you resolve common issues when installing and running APIC.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Network and Timeout Errors](#network-and-timeout-errors)
3. [Python Version Issues](#python-version-issues)
4. [Database Issues](#database-issues)
5. [API Key and Configuration Issues](#api-key-and-configuration-issues)

---

## Installation Issues

### Problem: Pip installation timeouts

**Symptoms:**
```
TimeoutError: The read operation timed out
File "/usr/local/lib/python3.11/site-packages/urllib3/response.py", line 561, in read
```

**Solutions:**

1. **Use the automated installation script** (Recommended):
   ```bash
   ./install.sh  # Linux/macOS
   # or
   install.bat  # Windows
   ```
   The script includes retry logic and extended timeouts.

2. **Manual installation with increased timeout:**
   ```bash
   pip install -r requirements.txt --timeout 300 --retries 5
   ```

3. **Use the pip configuration file:**
   ```bash
   export PIP_CONFIG_FILE=pip.conf  # Linux/macOS
   set PIP_CONFIG_FILE=pip.conf     # Windows
   pip install -r requirements.txt
   ```

4. **Install packages individually** if bulk installation fails:
   ```bash
   # Install core packages first
   pip install fastapi uvicorn sqlalchemy pydantic --timeout 300

   # Then install LangChain packages
   pip install langgraph langchain langchain-openai --timeout 300

   # Continue with remaining packages
   pip install -r requirements.txt --timeout 300
   ```

5. **Use a different PyPI mirror** if the default is slow:
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### Problem: Package installation fails with build errors

**Symptoms:**
```
ERROR: Failed building wheel for [package-name]
```

**Solutions:**

1. **Install binary packages** instead of building from source:
   ```bash
   pip install -r requirements.txt --prefer-binary
   ```

2. **Install build dependencies** (Linux):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install build-essential python3-dev

   # CentOS/RHEL
   sudo yum install gcc python3-devel
   ```

3. **Install build dependencies** (macOS):
   ```bash
   xcode-select --install
   brew install python
   ```

4. **Clear pip cache** if you suspect corruption:
   ```bash
   pip cache purge
   pip install -r requirements.txt
   ```

### Problem: Permission denied when running install.sh

**Symptoms:**
```
bash: ./install.sh: Permission denied
```

**Solution:**
```bash
chmod +x install.sh
./install.sh
```

---

## Network and Timeout Errors

### Problem: Slow or unstable network connection

**Solutions:**

1. **Use the pip configuration** with extended timeouts (already configured in `pip.conf`):
   - Timeout: 300 seconds (5 minutes)
   - Retries: 5 attempts
   - Prefer binary packages

2. **Download packages in smaller batches:**
   ```bash
   # Create a minimal requirements file
   cat > requirements-minimal.txt <<EOF
   fastapi>=0.115.0
   uvicorn[standard]>=0.30.0
   pydantic>=2.0.0
   EOF

   pip install -r requirements-minimal.txt
   pip install -r requirements.txt
   ```

3. **Use a local package cache** for repeated installations:
   ```bash
   # Download packages to a directory
   pip download -r requirements.txt -d ./pip-cache

   # Install from the cache
   pip install --no-index --find-links=./pip-cache -r requirements.txt
   ```

### Problem: Corporate firewall or proxy blocking PyPI

**Solutions:**

1. **Configure pip to use your proxy:**
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   pip install -r requirements.txt
   ```

2. **Add proxy to pip.conf:**
   ```ini
   [global]
   proxy = http://proxy.company.com:8080
   ```

3. **Use trusted host** if SSL certificates are blocked:
   ```bash
   pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
   ```

---

## Python Version Issues

### Problem: Python version too old

**Symptoms:**
```
Error: Python 3.11 or higher is required
Current version: 3.9.x
```

**Solutions:**

1. **Install Python 3.11 or 3.12:**

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install python3.11 python3.11-venv python3.11-dev
   ```

   **macOS:**
   ```bash
   brew install python@3.11
   ```

   **Windows:**
   - Download from [python.org](https://www.python.org/downloads/)

2. **Use pyenv** to manage multiple Python versions:
   ```bash
   # Install pyenv
   curl https://pyenv.run | bash

   # Install Python 3.11
   pyenv install 3.11.7
   pyenv local 3.11.7
   ```

3. **Create virtual environment with specific Python version:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

---

## Database Issues

### Problem: PostgreSQL connection refused

**Symptoms:**
```
sqlalchemy.exc.OperationalError: connection refused
```

**Solutions:**

1. **Ensure PostgreSQL is running:**
   ```bash
   # Check status
   sudo systemctl status postgresql  # Linux
   brew services list                 # macOS

   # Start if not running
   sudo systemctl start postgresql   # Linux
   brew services start postgresql    # macOS
   ```

2. **Check database credentials in .env:**
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/apic
   ```

3. **Create the database if it doesn't exist:**
   ```bash
   psql -U postgres
   CREATE DATABASE apic;
   \q
   ```

### Problem: Database tables not created

**Solutions:**

1. **Run Alembic migrations:**
   ```bash
   alembic upgrade head
   ```

2. **Check if migrations directory exists:**
   ```bash
   ls alembic/versions/
   ```

3. **Initialize Alembic if needed:**
   ```bash
   alembic init alembic
   ```

---

## API Key and Configuration Issues

### Problem: Missing API keys

**Symptoms:**
```
Error: OPENAI_API_KEY not found in environment
```

**Solutions:**

1. **Copy and configure .env file:**
   ```bash
   cp .env.example .env
   nano .env  # or use your preferred editor
   ```

2. **Set required API keys:**
   ```bash
   # In .env file
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   PINECONE_API_KEY=...
   ```

3. **Verify environment variables are loaded:**
   ```python
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
   ```

---

## Getting Additional Help

If you continue to experience issues:

1. **Run the installation verifier:**
   ```bash
   python -m src.utils.install_verifier
   ```

2. **Check the logs** for detailed error messages:
   ```bash
   # API logs
   tail -f logs/api.log

   # Frontend logs
   tail -f logs/frontend.log
   ```

3. **Create a GitHub issue** with:
   - Your Python version (`python --version`)
   - Your operating system
   - Complete error message
   - Steps to reproduce

4. **Common debugging commands:**
   ```bash
   # Check installed packages
   pip list

   # Verify Python imports
   python -c "import fastapi; import langchain; print('OK')"

   # Test database connection
   python -c "from src.utils.db_health import check_database_connection; print(check_database_connection())"
   ```

---

## Quick Reference

### Successful Installation Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All packages installed successfully
- [ ] PostgreSQL running
- [ ] .env file configured with API keys
- [ ] Database tables created
- [ ] Installation verifier passes all checks

### Essential Commands

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install with timeout protection
pip install -r requirements.txt --timeout 300 --retries 5

# Verify installation
python -m src.utils.install_verifier

# Start application
python main.py api      # Terminal 1
python main.py frontend # Terminal 2
```
