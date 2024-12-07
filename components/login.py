import requests
import qrcode
import time
import json
import os
from PIL import Image

# 添加请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.bilibili.com',
    'Accept': 'application/json, text/plain, */*',
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def generate_qrcode():
    """生成B站登录二维码"""
    try:
        # 获取二维码内容
        generate_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        response = requests.get(generate_url, headers=HEADERS)
        
        # 检查响应状态码
        if response.status_code != 200:
            raise Exception(f"请求失败，状态码: {response.status_code}")
            
        # 尝试解析JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("API响应内容:", response.text)
            raise Exception("API返回的数据不是有效的JSON格式")
            
        if data.get('code') != 0:
            raise Exception(f"获取二维码失败: {data.get('message', '未知错误')}")
            
        data = data['data']
        
        # 生成二维码
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data['url'])
        qr.make(fit=True)
        
        # 创建并保存二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("login_qr.png")
        
        # 在默认图片查看器中打开二维码
        Image.open("login_qr.png").show()
        
        return data['qrcode_key']
        
    except Exception as e:
        print(f"生成二维码时出错: {str(e)}")
        if os.path.exists("login_qr.png"):
            os.remove("login_qr.png")
        return None

def poll_login_status(qrcode_key):
    """轮询登录状态"""
    if not qrcode_key:
        return None
        
    poll_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    params = {'qrcode_key': qrcode_key}
    
    print("请使用B站手机APP扫描二维码登录...")
    
    try:
        while True:
            response = requests.get(poll_url, params=params, headers=HEADERS)  # 添加headers
            
            if response.status_code != 200:
                print(f"\n请求失败，状态码: {response.status_code}")
                break
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                print("\nAPI返回的数据不是有效的JSON格式")
                print("响应内容:", response.text)
                break
                
            if data.get('code') != 0:
                print(f"\nAPI错误: {data.get('message', '未知错误')}")
                break
                
            data = data['data']
            
            if data['code'] == 0:  # 成功登录
                print("\n登录成功！")
                cookies = response.cookies
                cookie_string = '; '.join([f'{cookie.name}={cookie.value}' for cookie in cookies])
                
                # 更新settings.py中的cookie
                if update_settings_cookie(cookie_string):
                    print("Cookie已更新到settings.py")
                else:
                    print("Cookie更新失败")
                
                # 清理二维码图片
                if os.path.exists("login_qr.png"):
                    os.remove("login_qr.png")
                    
                return cookie_string
                
            elif data['code'] == 86038:  # 二维码已过期
                print("\n二维码已过期，请重新运行程序")
                break
                
            elif data['code'] == 86090:  # 等待扫码
                print("\r等待扫码...", end='', flush=True)
                
            elif data['code'] == 86101:  # 等待确认
                print("\r等待确认登录...", end='', flush=True)
                
            time.sleep(2)
            
    except Exception as e:
        print(f"\n轮询登录状态时出错: {str(e)}")
    
    # 清理二维码图片
    if os.path.exists("login_qr.png"):
        os.remove("login_qr.png")
    return None

def get_bilibili_cookie():
    """获取B站登录cookie的主函数"""
    try:
        qrcode_key = generate_qrcode()
        if qrcode_key:
            cookie = poll_login_status(qrcode_key)
            return cookie
        return None
    except Exception as e:
        print(f"获取cookie失败: {str(e)}")
        return None

def update_settings_cookie(cookie_string):
    """更新settings.py中的BILIBILI_COOKIE"""
    try:
        # 读取现有的settings.py内容
        with open('../settings.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 查找BILIBILI_COOKIE的行
        cookie_found = False
        for i, line in enumerate(lines):
            if line.startswith('BILIBILI_COOKIE'):
                lines[i] = f'BILIBILI_COOKIE = "{cookie_string}"\n'
                cookie_found = True
                break
        
        # 如果没找到BILIBILI_COOKIE，就追加到文件末尾
        if not cookie_found:
            lines.append(f'\nBILIBILI_COOKIE = "{cookie_string}"\n')
        
        # 写回文件
        with open('../settings.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        return True
    except Exception as e:
        print(f"更新settings.py失败: {str(e)}")
        return False

if __name__ == "__main__":
    cookie = get_bilibili_cookie()
    if cookie:
        print(f"\nCookie已保存")
    else:
        print("\n获取Cookie失败") 