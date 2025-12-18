"""
Step 2: 下载并处理图片

从小红书下载图片，去除水印，调整尺寸
"""

from ..utils.logger import logger
from ..services.image_downloader import ImageDownloader


def download_and_process_images(xhs_data, target_count=6):
    """
    下载并处理图片（纯V2模式：仅从小红书获取）
    
    Args:
        xhs_data: 小红书搜索数据（包含images列表）
        target_count: 目标图片数量（默认6张）
    
    Returns:
        本地图片路径列表
    """
    images = xhs_data.get('images', [])
    
    if not images:
        raise ValueError("小红书数据中没有图片，无法继续")
    
    logger.info(f"Step 2: 下载并处理图片 - 来源: {len(images)}张，目标: {target_count}张")
    
    downloader = ImageDownloader()
    local_images = []
    
    # 处理图片，直到达到目标数量或所有图片处理完
    for i, img_url in enumerate(images, 1):
        if len(local_images) >= target_count:
            logger.info(f"已达到目标数量 {target_count} 张，停止处理")
            break
            
        try:
            logger.info(f"处理第{i}张图片...")
            
            # 下载并处理（去水印、调整尺寸）
            local_path = downloader.download_and_process(img_url, len(local_images) + 1)
            local_images.append(local_path)
            
            logger.info(f"  ✅ 已处理: {local_path}")
        
        except Exception as e:
            logger.warning(f"  ⚠️  处理失败: {e}，尝试下一张")
            continue
    
    if len(local_images) < target_count:
        logger.warning(f"⚠️  仅成功处理 {len(local_images)}/{target_count} 张图片")
    else:
        logger.info(f"✅ 成功处理 {len(local_images)} 张图片")
    
    if not local_images:
        raise ValueError("未能成功处理任何图片")
    
    return {
        'local_images': local_images,
        'downloader': downloader  # 保存downloader实例用于后续清理
    }

