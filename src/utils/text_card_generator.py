"""
文字卡片生成器

生成纯色背景的文字卡片图片
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont
from ..utils.logger import logger


class TextCardGenerator:
    """文字卡片生成器"""
    
    # 背景色方案（柔和、时尚的颜色）
    BACKGROUND_COLORS = [
        (255, 245, 240),  # 米白色
        (240, 248, 255),  # 浅蓝色
        (255, 250, 240),  # 花白色
        (245, 255, 250),  # 薄荷色
        (255, 240, 245),  # 淡粉色
        (240, 255, 240),  # 蜜瓜绿
        (255, 248, 220),  # 玉米丝色
        (230, 230, 250),  # 淡紫色
    ]
    
    # 文字色（深色，与背景形成对比）
    TEXT_COLORS = [
        (60, 60, 60),    # 深灰色
        (40, 40, 40),    # 炭灰色
        (80, 80, 80),    # 中灰色
    ]
    
    def __init__(self, output_dir="temp_images"):
        """初始化"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_card(self, text, emoji="", filename="text_card.jpg"):
        """
        生成文字卡片
        
        Args:
            text: 文字内容（7-12字）
            emoji: 表情符号（可选）
            filename: 输出文件名
        
        Returns:
            图片路径
        """
        # 随机选择配色
        bg_color = random.choice(self.BACKGROUND_COLORS)
        text_color = random.choice(self.TEXT_COLORS)
        
        # 创建图片（小红书推荐尺寸：3:4，适当减小尺寸加快上传）
        width, height = 1080, 1350
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # 尝试加载字体（优先使用系统字体）
        font_size = 80
        
        font = None
        try:
            # macOS 字体路径（支持中文和emoji）
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
                "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS Arial Unicode
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux 文泉驿
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux DejaVu
                "C:\\Windows\\Fonts\\msyh.ttc",  # Windows 微软雅黑
                "C:\\Windows\\Fonts\\simhei.ttf",  # Windows 黑体
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        logger.info(f"✅ 使用字体: {font_path}")
                        break
                    except Exception as e:
                        logger.debug(f"加载字体 {font_path} 失败: {e}")
                        continue
            
            if not font:
                logger.warning("⚠️  未找到系统字体，文字卡片可能显示不正常")
                # 如果没有找到字体，减小字号使用默认字体
                font_size = 40
                font = ImageFont.load_default()
        
        except Exception as e:
            logger.warning(f"⚠️  加载字体失败: {e}")
            font_size = 40
            font = ImageFont.load_default()
        
        # 组合文字和表情（如果没有找到合适字体，去掉emoji避免显示问题）
        if font and font != ImageFont.load_default():
            full_text = f"{emoji} {text}" if emoji else text
        else:
            # 使用默认字体时去掉emoji，只保留文字
            full_text = text
            logger.warning(f"⚠️  使用默认字体，已移除emoji: {emoji}")
        
        # 计算文字位置（居中）
        bbox = draw.textbbox((0, 0), full_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # 绘制文字
        draw.text((x, y), full_text, fill=text_color, font=font)
        
        # 保存图片（优化参数确保小红书能接受）
        output_path = os.path.join(self.output_dir, filename)
        
        # 保存为JPEG，质量85（平衡质量和文件大小）
        # optimize=True 可以减小文件大小
        image.save(output_path, 'JPEG', quality=85, optimize=True)
        
        # 验证图片文件
        file_size = os.path.getsize(output_path)
        logger.info(f"✅ 文字卡片已生成: {output_path}")
        logger.info(f"   文字: {full_text}")
        logger.info(f"   背景色: RGB{bg_color}")
        logger.info(f"   文件大小: {file_size / 1024:.1f} KB")
        
        return output_path
    
    def cleanup(self):
        """清理临时文件"""
        import glob
        pattern = os.path.join(self.output_dir, "text_card*.jpg")
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                logger.debug(f"已删除: {file}")
            except:
                pass

