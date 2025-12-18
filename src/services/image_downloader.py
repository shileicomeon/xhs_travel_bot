"""
图片下载和处理

从小红书下载图片并去除水印
"""

import os
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
from ..utils.logger import logger
from ..utils.retry import retry_on_network_error


class ImageDownloader:
    """图片下载器"""
    
    def __init__(self, output_dir: str = "temp_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    @retry_on_network_error
    def download_image(self, url: str, filename: str) -> str:
        """
        下载图片
        
        Args:
            url: 图片URL
            filename: 保存文件名
        
        Returns:
            本地文件路径
        """
        logger.info(f"下载图片: {url[:50]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 保存原图
        output_path = self.output_dir / filename
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"✅ 已保存: {output_path}")
        
        return str(output_path.absolute())
    
    def remove_watermark(self, image_path: str) -> str:
        """
        去除水印（简单裁剪底部）
        
        Args:
            image_path: 图片路径
        
        Returns:
            处理后的图片路径
        """
        logger.info(f"去除水印: {image_path}")
        
        try:
            img = Image.open(image_path)
            width, height = img.size
            
            # 小红书水印通常在底部，裁剪掉底部10%
            crop_height = int(height * 0.9)
            cropped = img.crop((0, 0, width, crop_height))
            
            # 保存处理后的图片
            output_path = image_path.replace('.jpg', '_no_watermark.jpg')
            cropped.save(output_path, 'JPEG', quality=95)
            
            logger.info(f"✅ 水印已去除: {output_path}")
            
            return output_path
        
        except Exception as e:
            logger.warning(f"去除水印失败: {e}，使用原图")
            return image_path
    
    def resize_for_xiaohongshu(self, image_path: str) -> str:
        """
        调整图片尺寸以符合小红书要求
        
        小红书图片要求:
        - 尺寸: 1000x1000 到 4096x4096
        - 宽高比: 0.5 到 2.0
        - 大小: ≤5MB
        
        Args:
            image_path: 图片路径
        
        Returns:
            处理后的图片路径
        """
        logger.info(f"调整图片尺寸: {image_path}")
        
        try:
            img = Image.open(image_path)
            width, height = img.size
            
            # 计算宽高比
            ratio = width / height
            
            # 目标尺寸（保持宽高比，最大边为2048）
            max_size = 2048
            
            if ratio > 1:  # 横图
                new_width = min(width, max_size)
                new_height = int(new_width / ratio)
            else:  # 竖图或方图
                new_height = min(height, max_size)
                new_width = int(new_height * ratio)
            
            # 确保在小红书要求范围内
            if new_width < 1000:
                new_width = 1000
                new_height = int(new_width / ratio)
            if new_height < 1000:
                new_height = 1000
                new_width = int(new_height * ratio)
            
            # 调整尺寸
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 保存
            output_path = image_path.replace('.jpg', '_resized.jpg')
            resized.save(output_path, 'JPEG', quality=90, optimize=True)
            
            # 检查文件大小
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            if file_size > 5:
                # 如果超过5MB，降低质量
                resized.save(output_path, 'JPEG', quality=80, optimize=True)
            
            logger.info(f"✅ 尺寸已调整: {new_width}x{new_height}")
            
            return output_path
        
        except Exception as e:
            logger.warning(f"调整尺寸失败: {e}，使用原图")
            return image_path
    
    def download_and_process(self, url: str, index: int) -> str:
        """
        下载并处理图片（完整流程）
        
        Args:
            url: 图片URL
            index: 图片索引
        
        Returns:
            处理后的本地图片路径
        """
        # 下载
        filename = f"image_{index:02d}.jpg"
        local_path = self.download_image(url, filename)
        
        # 去除水印
        no_watermark_path = self.remove_watermark(local_path)
        
        # 调整尺寸
        final_path = self.resize_for_xiaohongshu(no_watermark_path)
        
        return final_path
    
    def cleanup(self):
        """清理临时文件"""
        logger.info("清理临时图片文件...")
        
        try:
            import shutil
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
                logger.info("✅ 临时文件已清理")
        except Exception as e:
            logger.warning(f"清理失败: {e}")

