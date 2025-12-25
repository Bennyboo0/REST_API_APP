"""
Test Database Connection Script
Tests PostgreSQL connection using credentials from .env file
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


def test_database_connection():
    """Test database connection and display configuration."""

    # Load environment variables from .env file
    load_dotenv()

    # Get database credentials
    db_username = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")
    db_endpoint = os.getenv("DB_ENDPOINT")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")

    # Validate required variables
    missing = []
    if not db_username:
        missing.append("DB_USERNAME")
    if not db_password:
        missing.append("DB_PASSWORD")
    if not db_endpoint:
        missing.append("DB_ENDPOINT")
    if not db_name:
        missing.append("DB_NAME")

    if missing:
        print("❌ ERROR: Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease check your .env file and ensure all variables are set.")
        return False

    # Display configuration (hide password)
    print("=" * 70)
    print("DATABASE CONNECTION TEST")
    print("=" * 70)
    print(f"\n📋 Configuration:")
    print(f"   Username: {db_username}")
    print(f"   Password: {'*' * len(db_password)}")
    print(f"   Endpoint: {db_endpoint}")
    print(f"   Port:     {db_port}")
    print(f"   Database: {db_name}")

    # URL-encode password in case it has special characters
    encoded_password = quote_plus(db_password)

    # Construct database URL
    database_url = f"postgresql://{db_username}:{encoded_password}@{db_endpoint}:{db_port}/{db_name}"

    print(f"\n🔗 Connection String:")
    # Show URL with masked password
    masked_url = f"postgresql://{db_username}:***@{db_endpoint}:{db_port}/{db_name}"
    print(f"   {masked_url}")

    # Test connection
    print(f"\n🔄 Testing connection...")

    try:
        # Create engine
        engine = create_engine(database_url, echo=False)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]

            print("✅ Connection successful!")
            print(f"\n📊 PostgreSQL Version:")
            print(f"   {version}")

            # Test database access
            result = conn.execute(text("SELECT current_database();"))
            current_db = result.fetchone()[0]
            print(f"\n📁 Current Database:")
            print(f"   {current_db}")

            # Check if gematria_words table exists
            result = conn.execute(text("""
                                       SELECT EXISTS (SELECT
                                                      FROM information_schema.tables
                                                      WHERE table_name = 'gematria_words');
                                       """))
            table_exists = result.fetchone()[0]

            print(f"\n📋 Table Status:")
            if table_exists:
                print("   ✅ gematria_words table exists")

                # Get row count
                result = conn.execute(text("SELECT COUNT(*) FROM gematria_words;"))
                count = result.fetchone()[0]
                print(f"   📊 Records in table: {count}")
            else:
                print("   ⚠️  gematria_words table does not exist yet")
                print("   💡 Run 'python setup_db.py' to create tables")

        print("\n" + "=" * 70)
        print("✅ DATABASE CONNECTION TEST PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ Connection failed!")
        print(f"\n🔍 Error Details:")
        print(f"   {str(e)}")
        print(f"\n💡 Common Issues:")
        print("   1. Check if your credentials are correct")
        print("   2. Ensure your IP is whitelisted in AWS RDS security group")
        print("   3. Verify the database endpoint is correct")
        print("   4. Check if the database exists on the RDS instance")
        print("   5. Ensure the RDS instance is publicly accessible (if connecting remotely)")
        print("\n" + "=" * 70)
        print("❌ DATABASE CONNECTION TEST FAILED")
        print("=" * 70)
        return False


if __name__ == "__main__":
    test_database_connection()