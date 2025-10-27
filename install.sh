#!/bin/bash

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # بدون رنگ

# تابع چاپ با رنگ
print_step() {
    echo -e "${BLUE}[مرحله $1]${NC} ${CYAN}$2${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# هدر
clear
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}🤖  نصب و راه‌اندازی خودکار ربات VPN تلگرام${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# بررسی root
if [[ $EUID -ne 0 ]]; then
   print_warning "این اسکریپت نیاز به دسترسی root دارد."
   echo "لطفاً با sudo اجرا کنید: sudo ./install.sh"
   exit 1
fi

#!/bin/bash
set -e  # اگر خطایی رخ داد اسکریپت متوقف شود

# مسیر فعلی
CURRENT_DIR=$(pwd)

# بررسی اینکه پوشه پروژه وجود داشته باشه یا نه
if [ ! -f "bot.py" ] || [ ! -f "setup_bot.py" ] || [ ! -f "requirements.txt" ]; then
    echo "⏳ فایل‌های پروژه یافت نشد. در حال دانلود از گیت..."
    
    # پوشه موقت برای کلون کردن
    TMP_DIR=$(mktemp -d)
    
    git clone https://github.com/boleyla1/script-bot.git "$TMP_DIR/script-bot"
    
    # کپی همه فایل‌ها به پوشه فعلی
    cp -r "$TMP_DIR/script-bot/"* "$CURRENT_DIR/"
    
    # پاک کردن پوشه موقت
    rm -rf "$TMP_DIR"
    
    echo "✅ فایل‌های پروژه دانلود شدند."
fi


# مرحله 1: به‌روزرسانی سیستم
print_step 1 "به‌روزرسانی سیستم"
apt update -qq && apt upgrade -y -qq
print_success "سیستم به‌روزرسانی شد"

# مرحله 2: نصب Python و pip
print_step 2 "نصب Python 3 و pip"
apt install -y python3 python3-pip python3-venv -qq
print_success "Python نصب شد"

# بررسی نصب Python
python3 --version
pip3 --version

# مرحله 3: نصب MySQL Server
print_step 3 "نصب MySQL Server"

if ! command -v mysql &> /dev/null; then
    echo -e "${YELLOW}⏳ نصب MySQL Server...${NC}"
    apt install -y mysql-server -qq
    
    # راه‌اندازی MySQL
    systemctl start mysql
    systemctl enable mysql
    
    print_success "MySQL Server نصب شد"
    print_warning "لطفاً رمز عبور root برای MySQL تنظیم کنید:"
    mysql_secure_installation
else
    print_success "MySQL از قبل نصب است"
fi

# مرحله 4: ایجاد محیط مجازی Python
print_step 4 "ایجاد محیط مجازی Python"
python3 -m venv venv
source venv/bin/activate
print_success "محیط مجازی ایجاد شد"

# مرحله 5: نصب کتابخانه‌های Python
print_step 5 "نصب کتابخانه‌های مورد نیاز"

if [ ! -f "requirements.txt" ]; then
    print_error "فایل requirements.txt یافت نشد!"
    exit 1
fi

pip install --upgrade pip -q
pip install -r requirements.txt -q
print_success "کتابخانه‌های Python نصب شدند"

# مرحله 6: بررسی فایل‌های پروژه
print_step 6 "بررسی فایل‌های پروژه"

required_files=("bot.py" "setup_bot.py" "requirements.txt")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    print_error "فایل‌های زیر یافت نشدند:"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    exit 1
fi

print_success "همه فایل‌های مورد نیاز موجودند"

# مرحله 7: اجرای setup_bot.py
print_step 7 "راه‌اندازی دیتابیس و تنظیمات"
echo ""
print_warning "اکنون setup_bot.py اجرا می‌شود."
print_warning "لطفاً اطلاعات مورد نیاز را وارد کنید:"
echo ""

python3 setup_bot.py

# بررسی موفقیت‌آمیز بودن
if [ $? -ne 0 ]; then
    print_error "خطا در اجرای setup_bot.py"
    exit 1
fi

# مرحله 8: ایجاد سرویس systemd
print_step 8 "ایجاد سرویس systemd"

SERVICE_FILE="/etc/systemd/system/vpn-bot.service"
CURRENT_DIR=$(pwd)
PYTHON_PATH="$CURRENT_DIR/venv/bin/python3"

cat > $SERVICE_FILE <<EOF
[Unit]
Description=VPN Telegram Bot
After=network.target mysql.service

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$PYTHON_PATH $CURRENT_DIR/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vpn-bot
print_success "سرویس systemd ایجاد شد"

# خلاصه نهایی
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}✅ نصب با موفقیت کامل شد!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "${CYAN}📋 دستورات مفید:${NC}"
echo ""
echo -e "  ${YELLOW}▶ شروع ربات:${NC}"
echo -e "    sudo systemctl start vpn-bot"
echo ""
echo -e "  ${YELLOW}⏸ توقف ربات:${NC}"
echo -e "    sudo systemctl stop vpn-bot"
echo ""
echo -e "  ${YELLOW}🔄 ری‌استارت ربات:${NC}"
echo -e "    sudo systemctl restart vpn-bot"
echo ""
echo -e "  ${YELLOW}📊 وضعیت ربات:${NC}"
echo -e "    sudo systemctl status vpn-bot"
echo ""
echo -e "  ${YELLOW}📜 مشاهده لاگ‌ها:${NC}"
echo -e "    sudo journalctl -u vpn-bot -f"
echo ""
echo -e "${CYAN}🚀 برای شروع ربات:${NC}"
echo -e "  ${GREEN}sudo systemctl start vpn-bot${NC}"
echo ""
