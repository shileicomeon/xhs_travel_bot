"""
Step 4: 图文组装

将图片和文案组合成可发布格式
"""

import os
from ..utils.logger import logger


def assemble_post(images, content):
    """
    组装图文内容
    
    Args:
        images: 图片列表
        content: 文案内容
    
    Returns:
        {
            "images": [...],  # URL列表或本地路径列表
            "title": "...",
            "content": "...",
            "tags": [...],
            "is_local": bool
        }
    """
    logger.info("Step 4: 组装图文内容")
    
    # 判断是否需要处理图片
    need_process = should_process_images(images)
    
    if need_process:
        logger.info("图片需要处理（下载、裁剪、压缩）")
        image_paths = process_and_save_images(images)
        is_local = True
    else:
        logger.info("图片无需处理，直接使用URL")
        image_paths = [img['url'] for img in images]
        is_local = False
    
    # 组装
    post = {
        "images": image_paths,
        "title": content["title"],
        "content": content["content"],
        "tags": content["tags"],
        "is_local": is_local
    }
    
    logger.info(f"✅ 图文组装完成")
    logger.info(f"  图片数量: {len(image_paths)}")
    logger.info(f"  图片类型: {'本地文件' if is_local else 'URL'}")
    
    return post


def should_process_images(images):
    """
    判断是否需要处理图片
    
    简化版：总是使用URL（更快）
    如果需要处理，可以检查图片大小、格式等
    """
    # 简化版：直接使用URL
    return False


def process_and_save_images(images):
    """
    处理并保存所有图片到本地
    
    Returns:
        本地文件路径列表
    """
    processor = ImageProcessor()
    local_paths = []
    
    for i, img in enumerate(images):
        try:
            # 处理并保存
            local_path = processor.process_and_save(
                image_url=img["url"],
                index=i,
                img_type=img["type"]
            )
            local_paths.append(local_path)
        
        except Exception as e:
            logger.error(f"处理图片{i+1}失败: {e}")
            # 失败时使用原始URL
            local_paths.append(img["url"])
    
    return local_paths


def cleanup_local_images(image_paths):
    """清理本地临时图片"""
    for path in image_paths:
        if path.startswith("/tmp/") and os.path.exists(path):
            try:
                os.remove(path)
                logger.debug(f"删除临时文件: {path}")
            except Exception as e:
                logger.warning(f"删除临时文件失败: {path}, {e}")

