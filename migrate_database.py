# migrate_database.py
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import time

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


def table_exists(cursor, table_name):
    """بررسی وجود جدول"""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = %s
    """, (MYSQL_CONFIG['database'], table_name))
    return cursor.fetchone()[0] > 0


# ==================== ایجاد جداول اصلی ====================

def create_users_table(cursor, conn):
    """ایجاد جدول users"""
    print("🔄 بررسی جدول users...")

    if not table_exists(cursor, 'users'):
        print("  ➕ ایجاد جدول users...")
        cursor.execute('''CREATE TABLE users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            phone VARCHAR(20),
            balance INT DEFAULT 0,
            total_purchased INT DEFAULT 0,
            referral_code VARCHAR(50) UNIQUE,
            referred_by BIGINT DEFAULT NULL,
            is_blocked TINYINT(1) DEFAULT 0,
            user_tag VARCHAR(50) DEFAULT 'regular',
            admin_note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_referral (referral_code),
            INDEX idx_tag (user_tag),
            INDEX idx_referred (referred_by)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        conn.commit()
        print("  ✅ جدول users ایجاد شد")
    else:
        print("  ✓ جدول users موجود است")


def create_packages_table(cursor, conn):
    """ایجاد جدول packages"""
    print("🔄 بررسی جدول packages...")

    if not table_exists(cursor, 'packages'):
        print("  ➕ ایجاد جدول packages...")
        cursor.execute('''CREATE TABLE packages (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            duration INT NOT NULL COMMENT 'تعداد روز',
            traffic BIGINT NOT NULL COMMENT 'ترافیک به بایت',
            price INT NOT NULL,
            is_active TINYINT(1) DEFAULT 1,
            sort_order INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_active (is_active),
            INDEX idx_sort (sort_order)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')

        # وارد کردن پکیج‌های پیش‌فرض
        default_packages = [
            ("1month_30gb", "1 ماهه 30 گیگ", 30, 32212254720, 10000, 1, 1),
            ("1month_60gb", "1 ماهه 60 گیگ", 30, 64424509440, 90000, 1, 2),
            ("2month_100gb", "2 ماهه 100 گیگ", 60, 107374182400, 150000, 1, 3),
            ("3month_120gb", "3 ماهه 120 گیگ", 90, 128849018880, 250000, 1, 4),
            ("6month_300gb", "6 ماهه 300 گیگ", 180, 322122547200, 450000, 1, 5),
            ("12month_600gb", "1 ساله 600 گیگ", 365, 644245094400, 800000, 1, 6),
        ]

        cursor.executemany("""
            INSERT INTO packages (id, name, duration, traffic, price, is_active, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, default_packages)

        conn.commit()
        print("  ✅ جدول packages ایجاد شد و پکیج‌های پیش‌فرض وارد شدند")
    else:
        print("  ✓ جدول packages موجود است")


def create_orders_table(cursor, conn):
    """ایجاد جدول orders"""
    print("🔄 بررسی جدول orders...")

    if not table_exists(cursor, 'orders'):
        print("  ➕ ایجاد جدول orders...")
        cursor.execute('''CREATE TABLE orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            package_id VARCHAR(50),
            marzban_username VARCHAR(255),
            price INT,
            status VARCHAR(20),
            subscription_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            INDEX idx_user (user_id),
            INDEX idx_status (status),
            INDEX idx_marzban (marzban_username),
            INDEX idx_expires (expires_at),
            INDEX idx_package (package_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        conn.commit()
        print("  ✅ جدول orders ایجاد شد")
    else:
        print("  ✓ جدول orders موجود است")


def create_transactions_table(cursor, conn):
    """ایجاد جدول transactions"""
    print("🔄 بررسی جدول transactions...")

    if not table_exists(cursor, 'transactions'):
        print("  ➕ ایجاد جدول transactions...")
        cursor.execute('''CREATE TABLE transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            amount INT,
            type VARCHAR(50),
            description TEXT,
            admin_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user (user_id),
            INDEX idx_type (type),
            INDEX idx_admin (admin_id),
            INDEX idx_date (created_at),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        conn.commit()
        print("  ✅ جدول transactions ایجاد شد")
    else:
        print("  ✓ جدول transactions موجود است")


def create_payments_table(cursor, conn):
    """ایجاد جدول payments"""
    print("🔄 بررسی جدول payments...")

    if not table_exists(cursor, 'payments'):
        print("  ➕ ایجاد جدول payments...")
        cursor.execute('''CREATE TABLE payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            amount INT,
            authority VARCHAR(100),
            ref_id VARCHAR(100),
            status VARCHAR(20) DEFAULT 'pending',
            package_id VARCHAR(50),
            payment_type VARCHAR(20) DEFAULT 'package',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_authority (authority),
            INDEX idx_status (status),
            INDEX idx_user (user_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        conn.commit()
        print("  ✅ جدول payments ایجاد شد")
    else:
        print("  ✓ جدول payments موجود است")


def create_coupons_table(cursor, conn):
    """ایجاد جدول coupons"""
    print("🔄 بررسی جدول coupons...")

    if not table_exists(cursor, 'coupons'):
        print("  ➕ ایجاد جدول coupons...")
        cursor.execute('''CREATE TABLE coupons (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            type VARCHAR(20) NOT NULL,
            value INT NOT NULL,
            usage_limit INT DEFAULT NULL,
            used_count INT DEFAULT 0,
            expires_at TIMESTAMP DEFAULT NULL,
            is_active TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_code (code),
            INDEX idx_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        conn.commit()
        print("  ✅ جدول coupons ایجاد شد")
    else:
        print("  ✓ جدول coupons موجود است")


def create_coupon_usage_table(cursor, conn):
    """ایجاد جدول coupon_usage"""
    print("🔄 بررسی جدول coupon_usage...")

    if not table_exists(cursor, 'coupon_usage'):
        print("  ➕ ایجاد جدول coupon_usage...")
        cursor.execute('''CREATE TABLE coupon_usage (
            id INT AUTO_INCREMENT PRIMARY KEY,
            coupon_id INT,
            user_id BIGINT,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (coupon_id) REFERENCES coupons(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        conn.commit()
        print("  ✅ جدول coupon_usage ایجاد شد")
    else:
        print("  ✓ جدول coupon_usage موجود است")


def create_campaigns_table(cursor, conn):
    """ایجاد جدول campaigns"""
    print("🔄 بررسی جدول campaigns...")

    if not table_exists(cursor, 'campaigns'):
        print("  ➕ ایجاد جدول campaigns...")
        cursor.execute('''CREATE TABLE campaigns (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            bonus_percentage INT NOT NULL,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP NOT NULL,
            is_active TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        conn.commit()
        print("  ✅ جدول campaigns ایجاد شد")
    else:
        print("  ✓ جدول campaigns موجود است")


def create_admin_logs_table(cursor, conn):
    """ایجاد جدول admin_logs"""
    print("🔄 بررسی جدول admin_logs...")

    if not table_exists(cursor, 'admin_logs'):
        print("  ➕ ایجاد جدول admin_logs...")
        cursor.execute('''CREATE TABLE admin_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            admin_id BIGINT,
            action VARCHAR(255),
            target_user_id BIGINT DEFAULT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_admin (admin_id),
            INDEX idx_action (action),
            INDEX idx_date (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        conn.commit()
        print("  ✅ جدول admin_logs ایجاد شد")
    else:
        print("  ✓ جدول admin_logs موجود است")


def create_bot_settings_table(cursor, conn):
    """ایجاد جدول bot_settings"""
    print("🔄 بررسی جدول bot_settings...")

    if not table_exists(cursor, 'bot_settings'):
        print("  ➕ ایجاد جدول bot_settings...")
        cursor.execute('''CREATE TABLE bot_settings (
            setting_key VARCHAR(100) PRIMARY KEY,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')

        # تنظیمات پیش‌فرض
        default_settings = {
            'referral_inviter_reward': '10000',
            'referral_invited_reward': '5000',
            'welcome_message': 'به ربات VPN خوش آمدید! 🚀',
            'min_wallet_charge': '10000'
        }

        for key, value in default_settings.items():
            cursor.execute("""
                INSERT INTO bot_settings (setting_key, setting_value) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
            """, (key, value))

        conn.commit()
        print("  ✅ جدول bot_settings ایجاد شد")
    else:
        print("  ✓ جدول bot_settings موجود است")


# ==================== Migration جداول موجود ====================

def migrate_users_table(cursor, conn):
    """Migration جدول users"""
    print("🔄 بررسی ستون‌های جدول users...")

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

    # اضافه کردن admin_note
    if not column_exists(cursor, 'users', 'admin_note'):
        print("  ➕ اضافه کردن ستون admin_note...")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN admin_note TEXT AFTER user_tag
        """)
        changes_made = True
        print("  ✅ ستون admin_note اضافه شد")

    # اضافه کردن index برای user_tag
    if not index_exists(cursor, 'users', 'idx_tag'):
        print("  ➕ اضافه کردن index idx_tag...")
        cursor.execute("""
            ALTER TABLE users 
            ADD INDEX idx_tag (user_tag)
        """)
        changes_made = True
        print("  ✅ Index idx_tag اضافه شد")

    if changes_made:
        conn.commit()
        print("✅ تغییرات جدول users ذخیره شد\n")
    else:
        print("✓ جدول users به‌روز است\n")


def migrate_orders_table(cursor, conn):
    """Migration جدول orders"""
    print("🔄 بررسی indexهای جدول orders...")

    changes_made = False
    indexes = [
        ('idx_marzban', 'marzban_username'),
        ('idx_expires', 'expires_at'),
        ('idx_package', 'package_id')
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

    if changes_made:
        conn.commit()
        print("✅ تغییرات جدول orders ذخیره شد\n")
    else:
        print("✓ جدول orders به‌روز است\n")


def migrate_transactions_table(cursor, conn):
    """Migration جدول transactions"""
    print("🔄 بررسی indexهای جدول transactions...")

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

    if changes_made:
        conn.commit()
        print("✅ تغییرات جدول transactions ذخیره شد\n")
    else:
        print("✓ جدول transactions به‌روز است\n")


def migrate_payments_table(cursor, conn):
    """Migration جدول payments"""
    print("🔄 بررسی indexهای جدول payments...")

    changes_made = False

    if not index_exists(cursor, 'payments', 'idx_user'):
        print("  ➕ اضافه کردن index idx_user...")
        cursor.execute("""
            ALTER TABLE payments 
            ADD INDEX idx_user (user_id)
        """)
        changes_made = True
        print("  ✅ Index idx_user اضافه شد")

    if changes_made:
        conn.commit()
        print("✅ تغییرات جدول payments ذخیره شد\n")
    else:
        print("✓ جدول payments به‌روز است\n")


# ==================== بررسی نهایی ====================

def verify_database_structure(cursor):
    """بررسی نهایی ساختار دیتابیس"""
    print("🔍 بررسی نهایی ساختار دیتابیس...\n")

    # بررسی جدول packages
    print("📊 ساختار جدول packages:")
    cursor.execute("DESCRIBE packages")
    for row in cursor.fetchall():
        print(f"  {row[0]:20} {row[1]:30} {row[2]:10}")

    print("\n" + "=" * 70 + "\n")

    # بررسی جدول users
    print("📊 ساختار جدول users:")
    cursor.execute("DESCRIBE users")
    for row in cursor.fetchall():
        print(f"  {row[0]:20} {row[1]:30} {row[2]:10}")

    print("\n" + "=" * 70 + "\n")

    # شمارش رکوردها
    tables = [
        'users', 'packages', 'orders', 'transactions', 'payments',
        'coupons', 'coupon_usage', 'campaigns',
        'admin_logs', 'bot_settings'
    ]

    print("📈 تعداد رکوردها:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table:20} {count:>10} رکورد")
        except Error:
            print(f"  {table:20} {'جدول وجود ندارد':>20}")

    print("\n" + "=" * 70 + "\n")


# ==================== اجرای اصلی ====================

def main():
    """اجرای migration کامل"""
    print("=" * 70)
    print("🚀 شروع Migration دیتابیس VPN Bot با پشتیبانی مدیریت پکیج")
    print("=" * 70 + "\n")

    conn = None  # ✅ مقداردهی اولیه
    cursor = None  # ✅ مقداردهی اولیه

    try:
        # اتصال به دیتابیس
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        print(f"✅ اتصال به دیتابیس '{MYSQL_CONFIG['database']}' برقرار شد\n")

        # ایجاد جداول اصلی (ترتیب مهم است به خاطر Foreign Keys)
        create_users_table(cursor, conn)
        create_packages_table(cursor, conn)  # ← جدول جدید
        create_orders_table(cursor, conn)
        create_transactions_table(cursor, conn)
        create_payments_table(cursor, conn)
        create_coupons_table(cursor, conn)
        create_coupon_usage_table(cursor, conn)
        create_campaigns_table(cursor, conn)
        create_admin_logs_table(cursor, conn)
        create_bot_settings_table(cursor, conn)

        print("\n" + "=" * 70 + "\n")

        # اجرای migrationها برای جداول موجود
        migrate_users_table(cursor, conn)
        migrate_orders_table(cursor, conn)
        migrate_transactions_table(cursor, conn)
        migrate_payments_table(cursor, conn)

        # بررسی نهایی
        verify_database_structure(cursor)

        print("=" * 70)
        print("🎉 Migration با موفقیت کامل شد!")
        print("=" * 70)

        return True  # ✅ موفق

    except Error as e:
        print(f"\n❌ خطا در migration: {e}")
        return False

    finally:
        # ✅ بررسی قبل از بستن
        if conn is not None and conn.is_connected():
            if cursor is not None:
                cursor.close()
            conn.close()
            print("\n🔌 اتصال به دیتابیس بسته شد")


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
