# migrate_database.py
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

def column_exists(cursor, table, column):
    """بررسی وجود ستون در جدول"""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = %s 
        AND COLUMN_NAME = %s
    """, (MYSQL_CONFIG['database'], table, column))
    return cursor.fetchone()[0] > 0

def index_exists(cursor, table, index_name):
    """بررسی وجود index در جدول"""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.STATISTICS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = %s 
        AND INDEX_NAME = %s
    """, (MYSQL_CONFIG['database'], table, index_name))
    return cursor.fetchone()[0] > 0

def migrate_users_table(cursor, conn):
    """Migration جدول users"""
    print("🔄 بررسی جدول users...")
    
    changes_made = False
    
    # اضافه کردن user_tag
    if not column_exists(cursor, 'users', 'user_tag'):
        print("  ➕ اضافه کردن ستون user_tag...")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN user_tag VARCHAR(50) DEFAULT 'regular' AFTER is_blocked
        """)
        changes_made = True
        print("  ✅ ستون user_tag اضافه شد")
    else:
        print("  ✓ ستون user_tag موجود است")
    
    # اضافه کردن admin_note
    if not column_exists(cursor, 'users', 'admin_note'):
        print("  ➕ اضافه کردن ستون admin_note...")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN admin_note TEXT AFTER user_tag
        """)
        changes_made = True
        print("  ✅ ستون admin_note اضافه شد")
    else:
        print("  ✓ ستون admin_note موجود است")
    
    # اضافه کردن index برای user_tag
    if not index_exists(cursor, 'users', 'idx_tag'):
        print("  ➕ اضافه کردن index idx_tag...")
        cursor.execute("""
            ALTER TABLE users 
            ADD INDEX idx_tag (user_tag)
        """)
        changes_made = True
        print("  ✅ Index idx_tag اضافه شد")
    else:
        print("  ✓ Index idx_tag موجود است")
    
    if changes_made:
        conn.commit()
        print("✅ تغییرات جدول users ذخیره شد\n")
    else:
        print("✓ جدول users به‌روز است\n")

def migrate_orders_table(cursor, conn):
    """Migration جدول orders - اضافه کردن indexها"""
    print("🔄 بررسی جدول orders...")
    
    changes_made = False
    
    indexes = [
        ('idx_marzban', 'marzban_username'),
        ('idx_expires', 'expires_at')
    ]
    
    for index_name, column_name in indexes:
        if not index_exists(cursor, 'orders', index_name):
            print(f"  ➕ اضافه کردن index {index_name}...")
            cursor.execute(f"""
                ALTER TABLE orders 
                ADD INDEX {index_name} ({column_name})
            """)
            changes_made = True
            print(f"  ✅ Index {index_name} اضافه شد")
        else:
            print(f"  ✓ Index {index_name} موجود است")
    
    if changes_made:
        conn.commit()
        print("✅ تغییرات جدول orders ذخیره شد\n")
    else:
        print("✓ جدول orders به‌روز است\n")

def migrate_transactions_table(cursor, conn):
    """Migration جدول transactions - اضافه کردن indexها"""
    print("🔄 بررسی جدول transactions...")
    
    changes_made = False
    
    indexes = [
        ('idx_admin', 'admin_id'),
        ('idx_date', 'created_at')
    ]
    
    for index_name, column_name in indexes:
        if not index_exists(cursor, 'transactions', index_name):
            print(f"  ➕ اضافه کردن index {index_name}...")
            cursor.execute(f"""
                ALTER TABLE transactions 
                ADD INDEX {index_name} ({column_name})
            """)
            changes_made = True
            print(f"  ✅ Index {index_name} اضافه شد")
        else:
            print(f"  ✓ Index {index_name} موجود است")
    
    if changes_made:
        conn.commit()
        print("✅ تغییرات جدول transactions ذخیره شد\n")
    else:
        print("✓ جدول transactions به‌روز است\n")

def migrate_payments_table(cursor, conn):
    """Migration جدول payments - اضافه کردن index"""
    print("🔄 بررسی جدول payments...")
    
    changes_made = False
    
    if not index_exists(cursor, 'payments', 'idx_user'):
        print("  ➕ اضافه کردن index idx_user...")
        cursor.execute("""
            ALTER TABLE payments 
            ADD INDEX idx_user (user_id)
        """)
        changes_made = True
        print("  ✅ Index idx_user اضافه شد")
    else:
        print("  ✓ Index idx_user موجود است")
    
    if changes_made:
        conn.commit()
        print("✅ تغییرات جدول payments ذخیره شد\n")
    else:
        print("✓ جدول payments به‌روز است\n")

def create_settings_table(cursor, conn):
    """ایجاد جدول settings اگر وجود ندارد"""
    print("🔄 بررسی جدول settings...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            setting_key VARCHAR(100) PRIMARY KEY,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # تنظیمات پیش‌فرض
    default_settings = {
        'welcome_message': 'سلام {first_name}! 👋\n\nبه ربات VPN خوش آمدید.\n\n💰 موجودی شما: {balance} تومان',
        'referral_inviter_reward': '10000',
        'referral_invited_reward': '5000',
        'min_wallet_charge': '10000'
    }
    
    for key, value in default_settings.items():
        cursor.execute("""
            INSERT INTO settings (setting_key, setting_value) 
            VALUES (%s, %s) 
            ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
        """, (key, value))
    
    conn.commit()
    print("✅ جدول settings آماده است\n")

def create_admin_logs_table(cursor, conn):
    """ایجاد جدول admin_logs اگر وجود ندارد"""
    print("🔄 بررسی جدول admin_logs...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            admin_id BIGINT NOT NULL,
            action VARCHAR(100) NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_admin (admin_id),
            INDEX idx_action (action),
            INDEX idx_date (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    conn.commit()
    print("✅ جدول admin_logs آماده است\n")

def verify_database_structure(cursor):
    """بررسی نهایی ساختار دیتابیس"""
    print("🔍 بررسی نهایی ساختار دیتابیس...\n")
    
    # بررسی جدول users
    print("📊 ساختار جدول users:")
    cursor.execute("DESCRIBE users")
    for row in cursor.fetchall():
        print(f"  {row[0]:20} {row[1]:30} {row[2]:10}")
    
    print("\n" + "="*70 + "\n")
    
    # شمارش رکوردها
    tables = ['users', 'orders', 'transactions', 'payments', 'settings', 'admin_logs']
    print("📈 تعداد رکوردها:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table:20} {count:>10} رکورد")
        except Error:
            print(f"  {table:20} {'جدول وجود ندارد':>20}")
    
    print("\n" + "="*70 + "\n")

def main():
    """اجرای migration کامل"""
    print("="*70)
    print("🚀 شروع Migration دیتابیس VPN Bot")
    print("="*70 + "\n")
    
    try:
        # اتصال به دیتابیس
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        print(f"✅ اتصال به دیتابیس '{MYSQL_CONFIG['database']}' برقرار شد\n")
        
        # اجرای migrationها
        migrate_users_table(cursor, conn)
        migrate_orders_table(cursor, conn)
        migrate_transactions_table(cursor, conn)
        migrate_payments_table(cursor, conn)
        create_settings_table(cursor, conn)
        create_admin_logs_table(cursor, conn)
        
        # بررسی نهایی
        verify_database_structure(cursor)
        
        print("="*70)
        print("🎉 Migration با موفقیت کامل شد!")
        print("="*70)
        
    except Error as e:
        print(f"\n❌ خطا در migration: {e}")
        return False
        
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("\n🔌 اتصال به دیتابیس بسته شد")
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
