# From: Zero to AI Agent, Chapter 20, Section 20.1
# File: scripts/verify_setup.py

"""
Setup Verification Script

Run this to ensure your CASPAR development environment is properly configured.
"""

import sys
from pathlib import Path


def check_python_version():
    """Verify Python version is 3.11+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Verify all required packages are installed."""
    required = [
        ("langchain", "langchain"),
        ("langchain_openai", "langchain-openai"),
        ("langchain_text_splitters", "langchain-text-splitters"),
        ("langgraph", "langgraph"),
        ("chromadb", "chromadb"),
        ("fastapi", "fastapi"),
        ("pydantic_settings", "pydantic-settings"),
        ("structlog", "structlog"),
        ("psycopg", "psycopg"),
    ]
    
    all_good = True
    for module_name, package_name in required:
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - run: pip install {package_name}")
            all_good = False
    
    return all_good


def check_caspar_installed():
    """Verify the caspar package is installed in editable mode."""
    try:
        import caspar
        print("✅ caspar package is installed")
        return True
    except ImportError:
        print("❌ caspar package not found")
        print("   Run: pip install -e .")
        print("   (Make sure you're in the project root where pyproject.toml is)")
        return False


def check_env_file():
    """Verify .env file exists and has required variables."""
    # Find .env relative to this script's location
    env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("   Create one with: OPENAI_API_KEY=sk-your-key-here")
        return False
    
    content = env_path.read_text()
    
    if "OPENAI_API_KEY" not in content:
        print("❌ OPENAI_API_KEY not found in .env")
        return False
    
    if "sk-your" in content or "sk-xxx" in content:
        print("⚠️  .env found but OPENAI_API_KEY appears to be a placeholder")
        print("   Replace it with your actual API key")
        return False
    
    print("✅ .env file configured")
    return True


def check_configuration():
    """Verify configuration loads correctly."""
    try:
        from caspar.config import settings
        
        # Check that we can access settings
        _ = settings.openai_api_key
        _ = settings.default_model
        
        print(f"✅ Configuration loaded")
        print(f"   Environment: {settings.environment}")
        print(f"   Default model: {settings.default_model}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def check_openai_connection():
    """Verify OpenAI API connection works."""
    try:
        from caspar.config import settings
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model=settings.default_model,
            api_key=settings.openai_api_key,
            max_tokens=10
        )
        
        # Make a minimal test call
        response = llm.invoke("Say 'OK' and nothing else.")
        
        print(f"✅ OpenAI API connection successful")
        print(f"   Model: {settings.default_model}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return False


def check_database_connection():
    """Verify PostgreSQL database connection works."""
    try:
        import psycopg
        from caspar.config import settings
        
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"✅ PostgreSQL connection successful")
                print(f"   {version[:50]}...")
                return True
                
    except ImportError:
        print(f"❌ psycopg not installed - run: pip install psycopg")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure PostgreSQL is running: docker compose up -d")
        return False


def check_directory_structure():
    """Verify project directory structure is correct."""
    base_path = Path(__file__).parent.parent
    
    required_dirs = [
        "src/caspar/agent",
        "src/caspar/api",
        "src/caspar/knowledge",
        "src/caspar/tools",
        "src/caspar/handoff",
        "src/caspar/config",
        "tests/unit",
        "tests/integration",
        "tests/evaluation",
        "data/knowledge_base",
        "data/sample_data",
    ]
    
    all_good = True
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - missing")
            all_good = False
    
    return all_good


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("🔍 CASPAR Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("CASPAR Package", check_caspar_installed),
        ("Directory Structure", check_directory_structure),
        ("Environment File", check_env_file),
        ("Configuration", check_configuration),
        ("Database Connection", check_database_connection),
        ("OpenAI Connection", check_openai_connection),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        print("-" * 40)
        results.append(check_func())
    
    print("\n" + "=" * 60)
    
    if all(results):
        print("🎉 All checks passed! You're ready to build CASPAR!")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("   Refer to the setup instructions in Section 20.1")
    
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
