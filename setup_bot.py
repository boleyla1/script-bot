#!/usr/bin/env python3
# setup_bot.py - راه‌اندازی خودکار ربات VPN

import os
import sys
import getpass
import mysql.connector
from mysql.connector import Error

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 60)
    print("🤖  راه‌اندازی خودکار ربات VPN تلگرام")
    print("=" * 60)
    print(f"{Colors.END}\n")

def print_step(step_num, message):
    print(f"{Colors.BLUE}[مرحله {step_num}]{Colors.END} {Colors.BOLD}{message}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def test_mysql_connection(host, user, password, port=3306):
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port
        )
    except Error:
        return False
    return False

def create_database(host, user, password, db_name):
    """ایجاد دیتابیس MySQL"""
    try:
        connection = mysql.connector.connect(host=host, user=user, password=password)
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print_error(f"خطا در ایجاد دیتابیس: {e}")
        return False

def create_tables(host, user, password, db_name):
    """ایجاد جداول دیتابیس"""
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        cursor = connection.cursor()
        
        # جدول کاربران
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            phone VARCHAR(20),
            balance INT DEFAULT 0,
            total_purchased INT DEFAULT 0,
            referral_code VARCHAR(50) UNIQUE,
            referred_by BIGINT,
            is_blocked TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_referral (referral_code),
            INDEX idx_referred_by (referred_by)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        
        # جدول سفارشات
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
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
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        
        # جدول تراکنش‌ها
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            amount INT,
            type VARCHAR(50),
            description TEXT,
            admin_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user (user_id),
            INDEX idx_type (type),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        
        # جدول پرداخت‌ها
        cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
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
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print_error(f"خطا در ایجاد جداول: {e}")
        return False

def create_env_file(config):
    """ایجاد فایل .env با اطلاعات وارد شده"""
    env_content = f"""# Telegram Bot Configuration
TELEGRAM_TOKEN={config['telegram_token']}

# MySQL Database Configuration
MYSQL_HOST={config['mysql_host']}
MYSQL_PORT={config['mysql_port']}
MYSQL_DATABASE={config['mysql_database']}
MYSQL_USER={config['mysql_user']}
MYSQL_PASSWORD={config['mysql_password']}

# Marzban Panel Configuration
MARZBAN_URL={config['marzban_url']}
MARZBAN_USERNAME={config['marzban_username']}
MARZBAN_PASSWORD={config['marzban_password']}

# ZarinPal Payment Gateway
ZARINPAL_MERCHANT={config['zarinpal_merchant']}
ZARINPAL_SANDBOX={config['zarinpal_sandbox']}

# Admin User IDs (comma separated)
ADMIN_IDS={config['admin_ids']}
"""
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        return True
    except Exception as e:
        print_error(f"خطا در ایجاد فایل .env: {e}")
        return False

def select_or_create_database(host, user, password):
    """انتخاب دیتابیس موجود یا ایجاد دیتابیس جدید"""
    try:
        connection = mysql.connector.connect(host=host, user=user, password=password)
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        cursor.close()
        connection.close()
        
        print(f"\n{Colors.BOLD}📂 دیتابیس‌های موجود:{Colors.END}")
        for idx, db in enumerate(databases, 1):
            print(f"  {idx}. {db}")
        print(f"  {len(databases)+1}. ساخت دیتابیس جدید")
        
        choice = input(f"{Colors.CYAN}انتخاب کنید [1-{len(databases)+1}]: {Colors.END}").strip()
        
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(databases):
                selected_db = databases[choice-1]
                print_success(f"دیتابیس انتخاب شد: {selected_db}")
                return selected_db, False  # دیتابیس جدید ساخته نشده
            elif choice == len(databases)+1:
                new_db = input(f"{Colors.CYAN}نام دیتابیس جدید: {Colors.END}").strip()
                if create_database(host, user, password, new_db):
                    print_success(f"دیتابیس {new_db} ایجاد شد!")
                    return new_db, True  # دیتابیس جدید ساخته شده
        print_error("انتخاب نامعتبر!")
        sys.exit(1)
    except Error as e:
        print_error(f"خطا در دریافت دیتابیس‌ها: {e}")
        sys.exit(1)

def get_user_input():
    """دریافت اطلاعات از کاربر"""
    config = {}
    
    print_step(1, "تنظیمات ربات تلگرام")
    print_warning("توکن ربات را از @BotFather دریافت کنید")
    config['telegram_token'] = input(f"{Colors.CYAN}🤖 توکن ربات تلگرام: {Colors.END}").strip()
    
    config['admin_ids'] = input(f"{Colors.CYAN}👤 آیدی عددی ادمین (User ID): {Colors.END}").strip()
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    print_step(2, "تنظیمات دیتابیس MySQL")
    config['mysql_host'] = input(f"{Colors.CYAN}🖥️  آدرس MySQL [localhost]: {Colors.END}").strip() or 'localhost'
    config['mysql_port'] = input(f"{Colors.CYAN}🔌 پورت MySQL [3306]: {Colors.END}").strip() or '3306'
    
    print_warning("لطفاً یک کاربر MySQL با دسترسی کامل وارد کنید (معمولاً root)")
    config['mysql_user'] = input(f"{Colors.CYAN}👤 نام کاربری MySQL [root]: {Colors.END}").strip() or 'root'
    config['mysql_password'] = getpass.getpass(f"{Colors.CYAN}🔐 رمز عبور MySQL: {Colors.END}")
    
    # تست اتصال
    print(f"\n{Colors.YELLOW}⏳ تست اتصال به MySQL...{Colors.END}")
    if not test_mysql_connection(config['mysql_host'], config['mysql_user'], config['mysql_password']):
        print_error("اتصال به MySQL ناموفق بود! لطفاً اطلاعات را بررسی کنید.")
        sys.exit(1)
    print_success("اتصال به MySQL موفقیت‌آمیز بود!")
    
    # انتخاب یا ایجاد دیتابیس
    db_name, is_new = select_or_create_database(config['mysql_host'], config['mysql_user'], config['mysql_password'])
    config['mysql_database'] = db_name
    config['is_new_db'] = is_new
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    print_step(3, "تنظیمات پنل Marzban")
    print_warning("مثال: https://panel.example.com:8000")
    config['marzban_url'] = input(f"{Colors.CYAN}🌐 آدرس پنل Marzban: {Colors.END}").strip()
    config['marzban_username'] = input(f"{Colors.CYAN}👤 نام کاربری Marzban: {Colors.END}").strip()
    config['marzban_password'] = getpass.getpass(f"{Colors.CYAN}🔐 رمز عبور Marzban: {Colors.END}")
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    print_step(4, "تنظیمات درگاه پرداخت ZarinPal")
    config['zarinpal_merchant'] = input(f"{Colors.CYAN}💳 Merchant ID زرین‌پال: {Colors.END}").strip()
    
    sandbox = input(f"{Colors.CYAN}🧪 استفاده از حالت تست (sandbox)? [y/N]: {Colors.END}").strip().lower()
    config['zarinpal_sandbox'] = 'True' if sandbox == 'y' else 'False'
    
    return config

def main():
    try:
        print_header()
        
        config = get_user_input()
        
        # اگر دیتابیس جدید ساخته شد، جداول را ایجاد کن
        if config['is_new_db']:
            print_step(5, "ایجاد جداول دیتابیس")
            print(f"{Colors.YELLOW}⏳ در حال ایجاد جداول...{Colors.END}")
            if create_tables(config['mysql_host'], config['mysql_user'], 
                            config['mysql_password'], config['mysql_database']):
                print_success("جداول با موفقیت ایجاد شدند!")
            else:
                sys.exit(1)
        
        print_step(6, "ایجاد فایل .env")
        if create_env_file(config):
            print_success("فایل .env با موفقیت ایجاد شد!")
        else:
            sys.exit(1)
        
        # خلاصه نهایی
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*60}")
        print("✅ راه‌اندازی با موفقیت کامل شد!")
        print(f"{'='*60}{Colors.END}\n")
        
        print(f"{Colors.CYAN}📋 خلاصه تنظیمات:{Colors.END}")
        print(f"  🤖 توکن ربات: {config['telegram_token'][:20]}...")
        print(f"  💾 دیتابیس: {config['mysql_database']}")
        print(f"  🌐 پنل Marzban: {config['marzban_url']}")
        print(f"  💳 ZarinPal Merchant: {config['zarinpal_merchant'][:20]}...")
        
        print(f"\n{Colors.YELLOW}📌 برای اجرای ربات:{Colors.END}")
        print(f"  {Colors.BOLD}python3 bot.py{Colors.END}")
        
        print(f"\n{Colors.GREEN}🎉 ربات آماده است!{Colors.END}\n")
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  راه‌اندازی توسط کاربر لغو شد.{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print_error(f"خطای غیرمنتظره: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.version_info < (3, 7):
        print_error("این اسکریپت نیاز به Python 3.7 یا بالاتر دارد!")
        sys.exit(1)
    
    main()
