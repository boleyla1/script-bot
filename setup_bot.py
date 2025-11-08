#!/usr/bin/env python3
# setup_bot.py - راه‌اندازی خودکار ربات VPN

import os
import sys
import getpass
import mysql.connector
from mysql.connector import Error


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def clear():
    os.system('clear' if os.name == 'posix' else 'cls')


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def print_step(num, msg):
    print(f"\n{Colors.BOLD}{'=' * 60}")
    print(f"[مرحله {num}] {msg}")
    print(f"{'=' * 60}{Colors.RESET}")


def get_input(prompt, default=None, hide=False):
    if default:
        prompt = f"{Colors.CYAN}{prompt} [{default}]: {Colors.RESET}"
    else:
        prompt = f"{Colors.CYAN}{prompt}: {Colors.RESET}"

    if hide:
        value = getpass.getpass(prompt)
        return value if value else default
    else:
        value = input(prompt).strip()
        return value if value else default


def test_mysql_connection(host, port, user, password):
    """تست اتصال به MySQL"""
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        if connection.is_connected():
            connection.close()
            return True
    except Error:
        return False
    return False


def create_database(host, port, user, password, db_name):
    """ایجاد دیتابیس جدید"""
    try:
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print_error(f"خطا در ساخت دیتابیس: {e}")
        return False


def create_tables(host, port, user, password, db_name):
    """ایجاد جداول دیتابیس"""
    try:
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password, database=db_name
        )
        cursor = conn.cursor()

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

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print_error(f"خطا در ساخت جداول: {e}")
        return False


def create_env_file(config):
    """ایجاد فایل .env"""
    env_content = f"""# Telegram Bot Configuration
TELEGRAM_TOKEN={config['bot_token']}

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
        print_error(f"خطا در ساخت فایل .env: {e}")
        return False


def main():
    clear()
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 60)
    print("🤖  راه‌اندازی خودکار ربات VPN تلگرام")
    print("=" * 60)
    print(f"{Colors.RESET}\n")

    config = {}

    # ==================== مرحله 1: تنظیمات ربات ====================
    print_step(1, "تنظیمات ربات تلگرام")
    print_warning("توکن ربات را از @BotFather دریافت کنید")
    config['bot_token'] = get_input("🤖 توکن ربات تلگرام")
    config['admin_ids'] = get_input("👤 آیدی عددی ادمین (User ID)")

    # ==================== مرحله 2: تنظیمات دیتابیس MySQL ====================
    print_step(2, "تنظیمات دیتابیس MySQL")

    # ❗ اول بپرس جدید بسازه یا قبلی
    while True:
        db_choice = input("\nآیا می‌خواهید دیتابیس جدید بسازید؟ (y/n): ").strip().lower()
        if db_choice in ['y', 'n']:
            break
        print_warning("فقط y یا n وارد کنید!")

    # سپس اطلاعات MySQL بپرس
    config['mysql_host'] = get_input("🖥️  آدرس MySQL", "localhost")
    config['mysql_port'] = get_input("🔌 پورت MySQL", "3306")
    config['mysql_user'] = get_input("👤 نام کاربری MySQL", "root")
    config['mysql_password'] = get_input("🔐 رمز عبور MySQL", hide=True)

    print(f"\n{Colors.YELLOW}⏳ تست اتصال به MySQL...{Colors.RESET}")
    if not test_mysql_connection(config['mysql_host'], int(config['mysql_port']),
                                 config['mysql_user'], config['mysql_password']):
        print_error("اتصال به MySQL ناموفق بود! لطفاً اطلاعات را بررسی کنید.")
        sys.exit(1)
    print_success("اتصال به MySQL برقرار شد!")

    if db_choice == 'y':
        config['mysql_database'] = get_input("📦 نام دیتابیس جدید", "vpn_bot_db")
        if create_database(config['mysql_host'], int(config['mysql_port']),
                           config['mysql_user'], config['mysql_password'],
                           config['mysql_database']):
            print_success(f"دیتابیس '{config['mysql_database']}' ساخته شد!")
        else:
            sys.exit(1)
    else:
        config['mysql_database'] = get_input("📦 نام دیتابیس موجود", "vpn_bot_db")

    print(f"\n{Colors.YELLOW}⏳ ایجاد جداول دیتابیس...{Colors.RESET}")
    if create_tables(config['mysql_host'], int(config['mysql_port']),
                     config['mysql_user'], config['mysql_password'],
                     config['mysql_database']):
        print_success("جداول با موفقیت ایجاد شدند!")
    else:
        sys.exit(1)

    # ==================== مرحله 3: تنظیمات Marzban ====================
    print_step(3, "تنظیمات پنل Marzban")
    print_warning("مثال: https://panel.example.com:8000")
    config['marzban_url'] = get_input("🌐 آدرس پنل Marzban")
    config['marzban_username'] = get_input("👤 نام کاربری Marzban")
    config['marzban_password'] = get_input("🔐 رمز عبور Marzban", hide=True)

    # ==================== مرحله 4: تنظیمات ZarinPal ====================
    print_step(4, "تنظیمات درگاه پرداخت ZarinPal")
    config['zarinpal_merchant'] = get_input("💳 Merchant ID زرین‌پال")
    sandbox = get_input("🧪 استفاده از حالت تست (sandbox)? (y/n)", "n").lower()
    config['zarinpal_sandbox'] = 'True' if sandbox == 'y' else 'False'

    # ==================== مرحله 5: ایجاد فایل .env ====================
    print_step(5, "ایجاد فایل .env")
    if create_env_file(config):
        print_success("فایل .env با موفقیت ایجاد شد!")
    else:
        sys.exit(1)

    # ==================== خلاصه نهایی ====================
    print(f"\n{Colors.GREEN}{Colors.BOLD}")
    print("=" * 60)
    print("✅ راه‌اندازی با موفقیت کامل شد!")
    print("=" * 60)
    print(f"{Colors.RESET}\n")

    print(f"{Colors.CYAN}📋 خلاصه تنظیمات:{Colors.RESET}")
    print(f"  🤖 توکن ربات: {config['bot_token'][:20]}...")
    print(f"  💾 دیتابیس: {config['mysql_database']}")
    print(f"  🌐 پنل Marzban: {config['marzban_url']}")
    print(f"  💳 ZarinPal: {config['zarinpal_merchant'][:20]}...")

    print(f"\n{Colors.YELLOW}📌 برای اجرای ربات:{Colors.RESET}")
    print(f"  {Colors.BOLD}python3 bot.py{Colors.RESET}")

    print(f"\n{Colors.GREEN}🎉 ربات آماده است!{Colors.RESET}\n")


if __name__ == "__main__":
    try:
        if sys.version_info < (3, 7):
            print_error("این اسکریپت نیاز به Python 3.7 یا بالاتر دارد!")
            sys.exit(1)
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  راه‌اندازی توسط کاربر لغو شد.{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"خطای غیرمنتظره: {e}")
        sys.exit(1)
