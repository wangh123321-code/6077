-- 创建枚举类型
CREATE TYPE user_role AS ENUM ('user', 'staff', 'admin');
CREATE TYPE cat_room_status AS ENUM ('available', 'occupied', 'maintenance', 'cleaning');
CREATE TYPE service_type AS ENUM ('basic', 'addon');
CREATE TYPE booking_status AS ENUM ('pending', 'confirmed', 'paid', 'checked_in', 'checked_out', 'cancelled', 'refunded');
CREATE TYPE booking_service_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');
CREATE TYPE payment_method AS ENUM ('wechat', 'alipay', 'card', 'balance', 'cash');
CREATE TYPE payment_status AS ENUM ('pending', 'success', 'failed', 'refunded');
CREATE TYPE refund_status AS ENUM ('pending', 'approved', 'rejected', 'completed');

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50),
    avatar VARCHAR(255),
    role user_role NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_role ON users(role);

-- 猫屋表
CREATE TABLE cat_rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    price_per_day NUMERIC(10,2) NOT NULL,
    facilities VARCHAR[],
    images VARCHAR[],
    status cat_room_status NOT NULL DEFAULT 'available',
    area NUMERIC(5,2),
    floor INTEGER,
    location VARCHAR(200),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_cat_rooms_status ON cat_rooms(status);
CREATE INDEX idx_cat_rooms_price ON cat_rooms(price_per_day);
CREATE INDEX idx_cat_rooms_floor ON cat_rooms(floor);

-- 服务表
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    price NUMERIC(10,2) NOT NULL,
    type service_type NOT NULL DEFAULT 'basic',
    duration INTEGER,
    applicable_scene VARCHAR(200),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_services_type ON services(type);
CREATE INDEX idx_services_price ON services(price);

-- 会员表
CREATE TABLE members (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    level INTEGER NOT NULL DEFAULT 1,
    points INTEGER NOT NULL DEFAULT 0,
    balance NUMERIC(10,2) NOT NULL DEFAULT 0,
    valid_until DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_members_user_id ON members(user_id);
CREATE INDEX idx_members_level ON members(level);

-- 猫咪信息表
CREATE TABLE cat_infos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name VARCHAR(50) NOT NULL,
    breed VARCHAR(50),
    age INTEGER,
    gender VARCHAR(10),
    weight NUMERIC(5,2),
    vaccine_status VARCHAR[],
    health_record TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_cat_infos_user_id ON cat_infos(user_id);

-- 预订表
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(32) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    cat_room_id INTEGER NOT NULL REFERENCES cat_rooms(id),
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    cat_name VARCHAR(50),
    cat_age INTEGER,
    cat_food_brand VARCHAR(100),
    special_requirements VARCHAR(500),
    status booking_status NOT NULL DEFAULT 'pending',
    total_price NUMERIC(10,2) NOT NULL,
    verify_code VARCHAR(32) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_bookings_order_no ON bookings(order_no);
CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_cat_room_id ON bookings(cat_room_id);
CREATE INDEX idx_bookings_check_in ON bookings(check_in_date);
CREATE INDEX idx_bookings_check_out ON bookings(check_out_date);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_verify_code ON bookings(verify_code);

-- 唯一约束：防止同一猫屋同一时间重复预订
CREATE UNIQUE INDEX unique_room_date_booking 
ON bookings(cat_room_id, check_in_date, check_out_date)
WHERE status NOT IN ('cancelled', 'refunded');

-- 预订服务表
CREATE TABLE booking_services (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL REFERENCES bookings(id),
    service_id INTEGER NOT NULL REFERENCES services(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    price NUMERIC(10,2) NOT NULL,
    execute_time TIMESTAMP,
    executor_id INTEGER REFERENCES users(id),
    status booking_service_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_booking_services_booking_id ON booking_services(booking_id);
CREATE INDEX idx_booking_services_service_id ON booking_services(service_id);
CREATE INDEX idx_booking_services_executor_id ON booking_services(executor_id);
CREATE INDEX idx_booking_services_status ON booking_services(status);

-- 支付记录表
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(32) NOT NULL REFERENCES bookings(order_no),
    payment_method payment_method NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    transaction_id VARCHAR(100) UNIQUE,
    status payment_status NOT NULL DEFAULT 'pending',
    callback_data TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_payments_order_no ON payments(order_no);
CREATE INDEX idx_payments_transaction_id ON payments(transaction_id);
CREATE INDEX idx_payments_status ON payments(status);

-- 退款记录表
CREATE TABLE refunds (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(32) NOT NULL REFERENCES bookings(order_no),
    refund_amount NUMERIC(10,2) NOT NULL,
    refund_reason VARCHAR(500),
    status refund_status NOT NULL DEFAULT 'pending',
    approver_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_refunds_order_no ON refunds(order_no);
CREATE INDEX idx_refunds_status ON refunds(status);
CREATE INDEX idx_refunds_approver_id ON refunds(approver_id);

-- 插入20间猫屋测试数据
INSERT INTO cat_rooms (name, description, price_per_day, facilities, images, status, area, floor, location) VALUES
('豪华单间1号', '独立空调，全景窗，豪华猫爬架', 199.00, ARRAY['空调', '全景窗', '猫爬架', '自动饮水机', '监控摄像头'], ARRAY['/images/room1_1.jpg', '/images/room1_2.jpg'], 'available', 8.5, 1, 'A区101'),
('豪华单间2号', '独立空调，全景窗，豪华猫爬架', 199.00, ARRAY['空调', '全景窗', '猫爬架', '自动饮水机', '监控摄像头'], ARRAY['/images/room2_1.jpg', '/images/room2_2.jpg'], 'available', 8.5, 1, 'A区102'),
('豪华单间3号', '独立空调，全景窗，豪华猫爬架', 199.00, ARRAY['空调', '全景窗', '猫爬架', '自动饮水机', '监控摄像头'], ARRAY['/images/room3_1.jpg', '/images/room3_2.jpg'], 'available', 8.5, 1, 'A区103'),
('豪华单间4号', '独立空调，全景窗，豪华猫爬架', 199.00, ARRAY['空调', '全景窗', '猫爬架', '自动饮水机', '监控摄像头'], ARRAY['/images/room4_1.jpg', '/images/room4_2.jpg'], 'available', 8.5, 1, 'A区104'),
('豪华单间5号', '独立空调，全景窗，豪华猫爬架', 199.00, ARRAY['空调', '全景窗', '猫爬架', '自动饮水机', '监控摄像头'], ARRAY['/images/room5_1.jpg', '/images/room5_2.jpg'], 'available', 8.5, 1, 'A区105'),
('标准单间1号', '独立空调，舒适猫窝', 129.00, ARRAY['空调', '猫窝', '饮水机', '监控摄像头'], ARRAY['/images/room6_1.jpg', '/images/room6_2.jpg'], 'available', 6.0, 2, 'B区201'),
('标准单间2号', '独立空调，舒适猫窝', 129.00, ARRAY['空调', '猫窝', '饮水机', '监控摄像头'], ARRAY['/images/room7_1.jpg', '/images/room7_2.jpg'], 'available', 6.0, 2, 'B区202'),
('标准单间3号', '独立空调，舒适猫窝', 129.00, ARRAY['空调', '猫窝', '饮水机', '监控摄像头'], ARRAY['/images/room8_1.jpg', '/images/room8_2.jpg'], 'available', 6.0, 2, 'B区203'),
('标准单间4号', '独立空调，舒适猫窝', 129.00, ARRAY['空调', '猫窝', '饮水机', '监控摄像头'], ARRAY['/images/room9_1.jpg', '/images/room9_2.jpg'], 'available', 6.0, 2, 'B区204'),
('标准单间5号', '独立空调，舒适猫窝', 129.00, ARRAY['空调', '猫窝', '饮水机', '监控摄像头'], ARRAY['/images/room10_1.jpg', '/images/room10_2.jpg'], 'available', 6.0, 2, 'B区205'),
('家庭套房1号', '超大空间，可容纳2只猫，独立卫浴', 299.00, ARRAY['空调', '全景窗', '双层猫爬架', '自动喂食器', '监控摄像头', '猫砂盆'], ARRAY['/images/room11_1.jpg', '/images/room11_2.jpg'], 'available', 12.0, 1, 'C区101'),
('家庭套房2号', '超大空间，可容纳2只猫，独立卫浴', 299.00, ARRAY['空调', '全景窗', '双层猫爬架', '自动喂食器', '监控摄像头', '猫砂盆'], ARRAY['/images/room12_1.jpg', '/images/room12_2.jpg'], 'available', 12.0, 1, 'C区102'),
('家庭套房3号', '超大空间，可容纳2只猫，独立卫浴', 299.00, ARRAY['空调', '全景窗', '双层猫爬架', '自动喂食器', '监控摄像头', '猫砂盆'], ARRAY['/images/room13_1.jpg', '/images/room13_2.jpg'], 'available', 12.0, 1, 'C区103'),
('VIP总统套房', '顶级配置，专属管家服务，24小时直播', 599.00, ARRAY['中央空调', '全景落地窗', '豪华猫爬架', '自动喂食器', '自动饮水机', '24小时直播', '空气净化器', '猫砂盆'], ARRAY['/images/room14_1.jpg', '/images/room14_2.jpg'], 'available', 20.0, 3, 'D区301'),
('阳光房1号', '南向阳光充足，落地窗，适合晒猫', 169.00, ARRAY['空调', '落地窗', '猫爬架', '饮水机', '监控摄像头', '晒太阳平台'], ARRAY['/images/room15_1.jpg', '/images/room15_2.jpg'], 'available', 7.5, 3, 'E区301'),
('阳光房2号', '南向阳光充足，落地窗，适合晒猫', 169.00, ARRAY['空调', '落地窗', '猫爬架', '饮水机', '监控摄像头', '晒太阳平台'], ARRAY['/images/room16_1.jpg', '/images/room16_2.jpg'], 'available', 7.5, 3, 'E区302'),
('阳光房3号', '南向阳光充足，落地窗，适合晒猫', 169.00, ARRAY['空调', '落地窗', '猫爬架', '饮水机', '监控摄像头', '晒太阳平台'], ARRAY['/images/room17_1.jpg', '/images/room17_2.jpg'], 'available', 7.5, 3, 'E区303'),
('猫咪公寓1号', '经济实惠，温馨舒适', 89.00, ARRAY['空调', '猫窝', '饮水机', '监控摄像头'], ARRAY['/images/room18_1.jpg', '/images/room18_2.jpg'], 'available', 4.5, 2, 'F区201'),
('猫咪公寓2号', '经济实惠，温馨舒适', 89.00, ARRAY['空调', '猫窝', '饮水机', '监控摄像头'], ARRAY['/images/room19_1.jpg', '/images/room19_2.jpg'], 'available', 4.5, 2, 'F区202'),
('猫咪公寓3号', '经济实惠，温馨舒适', 89.00, ARRAY['空调', '猫窝', '饮水机', '监控摄像头'], ARRAY['/images/room20_1.jpg', '/images/room20_2.jpg'], 'available', 4.5, 2, 'F区203');

-- 插入基础服务数据
INSERT INTO services (name, description, price, type, duration, applicable_scene) VALUES
('基础护理', '每日梳毛、清洁眼睛、清洁耳朵', 30.00, 'basic', 15, '日常护理'),
('猫粮喂养', '提供高品质猫粮，每日三餐', 20.00, 'basic', 10, '日常喂养'),
('猫砂更换', '每日更换猫砂，保持卫生', 15.00, 'basic', 10, '日常卫生'),
('健康检查', '每日体温、精神状态检查', 25.00, 'basic', 10, '健康监测'),
('视频互动', '每日15分钟视频互动服务', 20.00, 'addon', 15, '主人远程互动'),
('专业洗澡', '专业猫咪洗澡、吹干、梳理', 128.00, 'addon', 60, '猫咪清洁美容'),
('SPA护理', '猫咪SPA按摩，舒缓放松', 198.00, 'addon', 45, '高端护理'),
('寄养接送', '市区内上门接送服务', 80.00, 'addon', 30, '交通服务'),
('医疗陪护', '如需就医，专人陪同就诊', 200.00, 'addon', 120, '特殊需求'),
('节日装饰', '节日主题房间布置服务', 50.00, 'addon', 20, '节日庆祝');
