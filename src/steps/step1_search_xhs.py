"""
Step 1: 从小红书搜索真实内容

使用MCP工具搜索小红书，获取真实的旅游内容和图片
"""

from ..utils.logger import logger
from ..services.xhs_mcp_client import XhsMcpClient, run_async


def search_xhs_content(ctx):
    """
    从小红书搜索内容
    
    Args:
        ctx: 上下文（包含city、topic_name、topic_type等信息）
    
    Returns:
        {
            'feeds': [帖子列表],
            'selected_feed': 选中的帖子详情,
            'images': 图片URL列表
        }
    """
    city = ctx['city']
    topic_name = ctx.get('topic_name', '旅游攻略')
    topic_type = ctx.get('topic_type', 'general')
    
    logger.info(f"Step 1: 从小红书搜索内容 - {city} {topic_name} ({topic_type})")
    
    client = XhsMcpClient()
    
    # 🆕 根据主题类型构建搜索关键词
    if topic_type == 'landmark':
        # 景点类：强调攻略、打卡、游玩
        keywords = [
            f"{city}{topic_name}攻略",
            f"{city}{topic_name}游玩",
            f"{topic_name}打卡"
        ]
    elif topic_type == 'food':
        # 美食类：强调推荐、探店、好吃
        keywords = [
            f"{city}{topic_name}推荐",
            f"{city}{topic_name}探店",
            f"{city}好吃的{topic_name}"
        ]
    elif topic_type == 'drink':
        # 饮品类：强调探店、推荐、咖啡馆/茶馆
        keywords = [
            f"{city}{topic_name}探店",
            f"{city}{topic_name}推荐",
            f"{city}{topic_name}店"
        ]
    else:  # general
        # 通用类：保持原有的旅游攻略关键词
        keywords = [
            f"{city}旅游攻略",
            f"{city}一日游",
            f"{city}必去景点"
        ]
    
    all_feeds = []
    
    # 搜索多个关键词
    for keyword in keywords:
        try:
            logger.info(f"搜索: {keyword}")
            feeds = run_async(client.search_feeds(keyword, limit=5))
            all_feeds.extend(feeds)
            
            if len(all_feeds) >= 3:
                break
        
        except Exception as e:
            logger.warning(f"搜索失败: {e}")
            continue
    
    if not all_feeds:
        logger.error("未找到任何内容")
        raise ValueError("小红书搜索无结果")
    
    logger.info(f"✅ 共找到 {len(all_feeds)} 个相关内容")
    
    # 策略：从多个帖子混合收集图片（降低重复率，避免侵权风险）
    all_images = []
    reference_titles = []
    reference_tags = []
    
    logger.info(f"从 {len(all_feeds)} 个帖子中提取图片...")
    
    for feed in all_feeds:
        feed_id = feed.get('feed_id', 'N/A')
        xsec_token = feed.get('xsec_token', '')
        
        try:
            if xsec_token:
                # 尝试获取详情
                detail = run_async(client.get_feed_detail(feed_id, xsec_token))
                
                if detail:
                    images = detail.get('images', [])
                    if images:
                        # 从每个帖子取部分图片（不是全部），增加多样性
                        take_count = min(len(images), 3)  # 每个帖子最多取3张
                        all_images.extend(images[:take_count])
                        reference_titles.append(detail.get('title', ''))
                        reference_tags.extend(detail.get('tags', []))
                        
                        logger.info(f"  ✅ 从帖子 {feed_id[:20]}... 获取 {take_count} 张图片")
                    else:
                        logger.warning(f"  ⚠️  帖子 {feed_id[:20]}... 没有图片")
            else:
                # 没有token，跳过
                logger.warning(f"  ⚠️  帖子 {feed_id[:20]}... 缺少xsec_token，跳过")
                
        except Exception as e:
            logger.warning(f"  ⚠️  获取帖子 {feed_id[:20]}... 失败: {e}")
            continue
    
    # 如果没有获取到图片，直接抛出异常
    if not all_images:
        error_msg = (
            f"未能从小红书获取任何图片。\n"
            f"原因：所有 {len(all_feeds)} 个帖子都无法获取图片。\n"
            f"解决方案：\n"
            f"  1. 更新小红书MCP服务到最新版本\n"
            f"  2. 确保MCP服务已正确登录\n"
            f"  3. 联系MCP服务提供商解决token问题"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"✅ 共获取 {len(all_images)} 张图片（混合自 {len([t for t in reference_titles if t])} 个帖子）")
    
    return {
        'feeds': all_feeds,
        'images': all_images[:10],  # 最多10张，后续会筛选到6张
        'reference_title': reference_titles[0] if reference_titles else f"{city}旅游攻略",
        'reference_content': '',  # 混合模式下不保存原文
        'reference_tags': list(set(reference_tags))[:10]  # 去重，最多10个
    }

