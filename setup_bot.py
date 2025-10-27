#!/usr/bin/env python3
# setup_bot.py - نصب و راه‌اندازی خودکار ربات VPN تلگرام

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

def print_step(step, msg):
    print(f"{Colors.BLUE}[مرحله {step}]{Colors.END} {Colors.CYAN}{msg}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def test_mysql_connection(host, user, password, port=3306):
    """تست اتصال به MySQL با پورت مشخص"""
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port
        )
        if connection.is_connected():
            connection.close()
            return True
    except Error as e:
        print_error(f"خطا در اتصال به MySQL: {e}")
        return False
    return False

def create_database(host, user, password, db_name, port=3306):
    """ایجاد دیتابیس جدید"""
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print_error(f"خطا در ایجاد دیتابیس: {e}")
        return False

def create_tables(host, user, password, db_name, port=3306):
    """ایجاد جداول مورد نیاز"""
    try:
        connection = mysql.connector.connect(
            host=host, user=user, password=password,
            database=db_name, port=port
        )
        cursor = connection.cursor()

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    """ایجاد فایل .env"""
    env_text = f"""# Telegram Bot Configuration
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

# Admin User IDs
ADMIN_IDS={config['admin_ids']}
"""
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_text)
        return True
    except Exception as e:
        print_error(f"خطا در ساخت فایل .env: {e}")
        return False

def get_user_input():
    """دریافت ورودی کاربر"""
    config = {}
    print_step(1, "تنظیمات ربات تلگرام")
    print_warning("توکن ربات را از @BotFather دریافت کنید")
    config['telegram_token'] = input(f"{Colors.CYAN}🤖 توکن ربات تلگرام: {Colors.END}").strip()
    config['admin_ids'] = input(f"{Colors.CYAN}👤 آیدی عددی ادمین (User ID): {Colors.END}").strip()

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}\n")

    print_step(2, "تنظیمات دیتابیس MySQL")
    config['mysql_host'] = input(f"{Colors.CYAN}🖥️  آدرس MySQL [localhost]: {Colors.END}").strip() or "localhost"
    config['mysql_port'] = input(f"{Colors.CYAN}🔌 پورت MySQL [3306]: {Colors.END}").strip() or "3306"

    print_warning("لطفاً یک کاربر MySQL با دسترسی کامل وارد کنید (معمولاً root)")
    config['mysql_user'] = input(f"{Colors.CYAN}👤 نام کاربری MySQL [root]: {Colors.END}").strip() or "root"
    config['mysql_password'] = getpass.getpass(f"{Colors.CYAN}🔐 رمز عبور MySQL: {Colors.END}")

    port = int(config['mysql_port'])
    print(f"\n{Colors.YELLOW}⏳ تست اتصال به MySQL...{Colors.END}")
    if not test_mysql_connection(config['mysql_host'], config['mysql_user'], config['mysql_password'], port):
        sys.exit(1)
    print_success("اتصال به MySQL موفق بود ✅")

    print(f"\n{Colors.CYAN}آیا می‌خواهید دیتابیس جدید بسازید یا از موجود استفاده کنید؟{Colors.END}")
    choice = input(f"{Colors.YELLOW}[y] ساخت جدید  /  [n] استفاده از موجود: {Colors.END}").lower().strip()

    if choice == 'y':
        config['mysql_database'] = input(f"{Colors.CYAN}📦 نام دیتابیس جدید: {Colors.END}").strip()
        if create_database(config['mysql_host'], config['mysql_user'], config['mysql_password'], config['mysql_database'], port):
            print_success("دیتابیس ساخته شد ✅")
            if create_tables(config['mysql_host'], config['mysql_user'], config['mysql_password'], config['mysql_database'], port):
                print_success("جداول با موفقیت ایجاد شدند ✅")
        else:
            sys.exit(1)
    else:
        config['mysql_database'] = input(f"{Colors.CYAN}📂 نام دیتابیس موجود: {Colors.END}").strip()
        print_success(f"از دیتابیس موجود ({config['mysql_database']}) استفاده می‌شود ✅")

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}\n")

    print_step(3, "تنظیمات پنل Marzban")
    config['marzban_url'] = input(f"{Colors.CYAN}🌐 آدرس پنل Marzban: {Colors.END}").strip()
    config['marzban_username'] = input(f"{Colors.CYAN}👤 نام کاربری Marzban: {Colors.END}").strip()
    config['marzban_password'] = getpass.getpass(f"{Colors.CYAN}🔐 رمز عبور Marzban: {Colors.END}")

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}\n")

    print_step(4, "تنظیمات درگاه زرین‌پال")
    config['zarinpal_merchant'] = input(f"{Colors.CYAN}💳 Merchant ID زرین‌پال: {Colors.END}").strip()
    sandbox = input(f"{Colors.CYAN}🧪 استفاده از حالت تست (sandbox)? [y/N]: {Colors.END}").lower().strip()
    config['zarinpal_sandbox'] = "True" if sandbox == "y" else "False"

    return config

def main():
    print_header()
    config = get_user_input()

    print_step(5, "ایجاد فایل .env")
    if create_env_file(config):
        print_success("فایل .env با موفقیت ساخته شد ✅")

    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ راه‌اندازی با موفقیت انجام شد!{Colors.END}")
    print(f"{Colors.CYAN}برای اجرای ربات دستور زیر را وارد کنید:{Colors.END}")
    print(f"{Colors.YELLOW}python3 bot.py{Colors.END}\n")

if __name__ == "__main__":
    if sys.version_info < (3, 7):
        print_error("این اسکریپت نیاز به Python 3.7 یا بالاتر دارد!")
        sys.exit(1)
    try:
        main()
    except KeyboardInterrupt:
        print_warning("راه‌اندازی لغو شد.")
        sys.exit(0)
