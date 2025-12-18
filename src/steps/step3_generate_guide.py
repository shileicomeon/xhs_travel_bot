"""
Step 3: 生成攻略式文案

基于小红书参考内容，生成专业的旅游攻略
"""

from ..utils.logger import logger
from ..services import get_ai_client
from ..prompts.guide_content import GUIDE_CONTENT_PROMPT


def generate_guide_content(ctx, xhs_data):
    """
    生成攻略式文案
    
    Args:
        ctx: 上下文
        xhs_data: 小红书数据
    
    Returns:
        {
            "title": "标题",
            "content": "正文",
            "tags": ["#标签1", "#标签2"]
        }
    """
    logger.info(f"Step 3: 生成攻略式文案 - {ctx['city']}")
    
    # 创建AI客户端
    ai_client = get_ai_client()
    
    # 提取地标信息
    landmarks = _extract_landmarks(ctx, xhs_data)
    
    # 构建参考内容（混合模式）
    reference_content = f"""
【参考信息】
参考标题: {xhs_data.get('reference_title', '')}

常见标签: {' '.join(xhs_data.get('reference_tags', [])[:5])}

【说明】
- 图片来自多个高质量旅游帖子，展示了{ctx['city']}的多个景点
- 请基于城市和地标信息生成原创内容
- 内容要实用、详细，不要空泛
"""
    
    # 构建prompt
    prompt = GUIDE_CONTENT_PROMPT.format(
        city=ctx['city'],
        reference_content=reference_content,
        image_count=len(xhs_data.get('images', [])),
        landmarks=', '.join(landmarks)
    )
    
    logger.debug(f"Prompt:\n{prompt[:200]}...")
    
    # 生成文案
    try:
        content = ai_client.generate_content_from_prompt(prompt)
        
        logger.info(f"✅ 攻略文案生成完成")
        logger.info(f"  标题: {content['title']}")
        logger.info(f"  标签: {', '.join(content['tags'])}")
        
        return content
    
    except Exception as e:
        logger.error(f"文案生成失败: {e}")
        # 返回备用文案
        return _generate_fallback_guide(ctx, landmarks)


def _extract_landmarks(ctx, xhs_data):
    """从上下文和参考内容中提取地标"""
    landmarks = []
    
    # 从城市配置获取
    city_keywords = ctx.get('keywords', {})
    city_landmarks = city_keywords.get('landmarks', [])
    landmarks.extend(city_landmarks[:3])
    
    # 从参考标题提取
    ref_title = xhs_data.get('reference_title', '')
    for landmark in city_landmarks:
        if landmark in ref_title and landmark not in landmarks:
            landmarks.append(landmark)
    
    return landmarks[:5]  # 最多5个


def _generate_fallback_guide(ctx, landmarks):
    """生成备用攻略文案"""
    logger.warning("使用备用攻略文案模板")
    
    city = ctx['city']
    landmarks_str = '、'.join(landmarks[:2]) if landmarks else '旅游'  # 最多2个地标
    
    # 生成标题（最多20字）
    title = f"{city}{landmarks_str}一日游攻略"
    if len(title) > 20:
        title = f"{city}旅游攻略"
    
    return {
        "title": title,
        "content": f"""今天给大家整理一份超详细的{city}攻略！

📍 景点推荐
{landmarks_str}都是必打卡的地方，每个景点都有独特的魅力。

🎫 门票信息
大部分景点门票在50-100元之间，建议提前网上购票更优惠。

⏰ 最佳游玩时间
建议早上9点开始，避开人流高峰，下午5点前结束。

🚇 交通方式
市区景点地铁直达，郊区景点建议包车或跟团。

💡 游玩建议
1. 穿舒适的鞋子，一天要走很多路
2. 带好防晒用品和水
3. 提前规划好路线，节省时间

⚠️ 注意事项
1. 节假日人多，尽量避开
2. 保管好随身物品
3. 注意景区开放时间

💡 实用Tips：
1. 提前一天预订门票，避免现场排队
2. 带上充电宝，拍照耗电快
3. 尝试当地特色美食，不要只吃连锁店""",
        "tags": [f"#{city}旅游[话题]#", f"#{city}攻略[话题]#", "#旅游指南[话题]#", "#必打卡[话题]#"]
    }

