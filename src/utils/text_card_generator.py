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
    
    # 背景色方案（更多彩的颜色）
    BACKGROUND_COLORS = [
        (255, 245, 240),  # 米白色
        (240, 248, 255),  # 浅蓝色
        (255, 250, 240),  # 花白色
        (245, 255, 250),  # 薄荷色
        (255, 240, 245),  # 淡粉色
        (240, 255, 240),  # 蜜瓜绿
        (255, 248, 220),  # 玉米丝色
        (230, 230, 250),  # 淡紫色
        (255, 228, 225),  # 浅玫瑰色
        (240, 255, 255),  # 天蓝色
        (255, 250, 205),  # 柠檬绸色
        (250, 240, 230),  # 亚麻色
        (245, 245, 220),  # 米黄色
        (255, 239, 213),  # 番木瓜色
        (230, 255, 250),  # 薄荷奶油色
    ]
    
    # 文字色方案（多种颜色，与背景形成对比）
    TEXT_COLORS = [
        (60, 60, 60),      # 深灰色
        (40, 40, 40),      # 炭灰色
        (80, 80, 80),      # 中灰色
        (70, 130, 180),    # 钢青色
        (188, 143, 143),   # 玫瑰褐色
        (139, 69, 19),     # 马鞍棕色
        (85, 107, 47),     # 橄榄绿
        (72, 61, 139),     # 深板岩蓝
        (112, 128, 144),   # 板岩灰
        (47, 79, 79),      # 深板岩灰
        (105, 105, 105),   # 暗灰色
        (128, 0, 0),       # 栗色
        (0, 100, 0),       # 深绿色
        (25, 25, 112),     # 午夜蓝
    ]
    
    # 根据关键词添加的装饰表情
    KEYWORD_EMOJIS = {
        '上班': ['💼', '👔', '⏰'],
        '辞职': ['🎉', '🆓', '✨'],
        '打工': ['💪', '🔥', '⚡'],
        '周五': ['🎊', '🎈', '🌟'],
        '周末': ['🎮', '🛋️', '☕'],
        '逃离': ['🏃', '🚀', '🌈'],
        '治愈': ['🌿', '🌸', '💚'],
        '旅行': ['✈️', '🗺️', '🎒'],
        '快乐': ['😊', '🌞', '💕'],
        '值得': ['💖', '⭐', '🌺'],
        '美好': ['🌸', '🌼', '🦋'],
        '发呆': ['💭', '☁️', '🌙'],
        '躺平': ['🛌', '😴', '💤'],
        '咸鱼': ['🐟', '😌', '🌊'],
        '梦想': ['💫', '🌠', '✨'],
        '远方': ['🌄', '🏔️', '🌅'],
    }
    
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
        
        # 根据文字内容智能添加装饰表情
        decoration_emoji = self._get_decoration_emoji(text)
        
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
        
        # 处理文字：支持自动换行（不添加emoji，避免显示为方框）
        lines = self._wrap_text(text, font, draw, width - 200)  # 留100px边距
        
        # 记录装饰表情（但不添加到图片中，emoji在标题和正文中体现）
        if decoration_emoji:
            logger.info(f"✨ 装饰表情（标题用）: {decoration_emoji}")
        
        if emoji:
            logger.info(f"ℹ️  原始emoji将在标题中体现: {emoji}")
        
        # 计算总高度
        line_height = font_size + 30  # 行间距
        total_height = len(lines) * line_height
        
        # 绘制每一行（垂直居中）
        start_y = (height - total_height) // 2
        
        for i, line in enumerate(lines):
            # 计算每行的水平居中位置
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = start_y + i * line_height
            
            # 绘制文字
            draw.text((x, y), line, fill=text_color, font=font)
        
        # 保存图片（优化参数确保小红书能接受）
        output_path = os.path.join(self.output_dir, filename)
        
        # 保存为JPEG，质量85（平衡质量和文件大小）
        # optimize=True 可以减小文件大小
        image.save(output_path, 'JPEG', quality=85, optimize=True)
        
        # 转换为绝对路径（确保MCP服务能找到文件）
        abs_output_path = os.path.abspath(output_path)
        
        # 验证图片文件
        file_size = os.path.getsize(abs_output_path)
        logger.info(f"✅ 文字卡片已生成: {abs_output_path}")
        logger.info(f"   文字: {text}")
        logger.info(f"   行数: {len(lines)}")
        logger.info(f"   背景色: RGB{bg_color}")
        logger.info(f"   文字色: RGB{text_color}")
        logger.info(f"   文件大小: {file_size / 1024:.1f} KB")
        
        return abs_output_path
    
    def _get_decoration_emoji(self, text):
        """
        根据文字内容智能选择装饰表情
        
        Args:
            text: 文字内容
        
        Returns:
            表情符号或空字符串
        """
        for keyword, emojis in self.KEYWORD_EMOJIS.items():
            if keyword in text:
                return random.choice(emojis)
        return ""
    
    def _wrap_text(self, text, font, draw, max_width):
        """
        自动换行
        
        Args:
            text: 文字内容
            font: 字体
            draw: 绘图对象
            max_width: 最大宽度
        
        Returns:
            换行后的文字列表
        """
        # 如果文字不长，直接返回
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            return [text]
        
        # 需要换行：按字符逐个测试
        lines = []
        current_line = ""
        
        for char in text:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                # 当前行已满，开始新行
                if current_line:
                    lines.append(current_line)
                current_line = char
        
        # 添加最后一行
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]
    
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

