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
    
    # 获取话题类型
    topic_type = ctx.get('topic_type', 'landmark')
    topic_type_desc = {
        'food': '美食',
        'hotel': '住宿',
        'activity': '活动/体验',
        'landmark': '景点'
    }.get(topic_type, '景点')
    
    logger.info(f"话题类型: {topic_type} ({topic_type_desc})")
    
    # 构建prompt
    prompt = GUIDE_CONTENT_PROMPT.format(
        city=ctx['city'],
        topic_type=topic_type,
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
        return _generate_fallback_guide(ctx, landmarks, topic_type)


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


def _generate_fallback_guide(ctx, landmarks, topic_type='landmark'):
    """生成备用攻略文案"""
    logger.warning(f"使用备用攻略文案模板 (类型: {topic_type})")
    
    city = ctx['city']
    topic_name = ctx.get('topic_name', '')
    landmarks_str = '、'.join(landmarks[:2]) if landmarks else topic_name or '旅游'  # 最多2个地标
    
    # 根据话题类型生成标题
    if topic_type == 'food':
        title = f"来{city}必吃的{landmarks_str}！"
    elif topic_type == 'hotel':
        title = f"{city}住宿攻略｜{landmarks_str}"
    elif topic_type == 'activity':
        title = f"{city}{landmarks_str}体验攻略"
    else:
        title = f"{city}{landmarks_str}一日游攻略"
    
    # 确保标题不超过20字
    if len(title) > 20:
        if topic_type == 'food':
            title = f"{city}美食攻略"
        elif topic_type == 'hotel':
            title = f"{city}住宿攻略"
        elif topic_type == 'activity':
            title = f"{city}玩乐攻略"
        else:
            title = f"{city}旅游攻略"
    
    # 根据话题类型生成不同风格的内容
    topic_type = ctx.get('topic_type', 'landmark')
    
    if topic_type == 'food':
        # 美食类攻略
        content = f"""来{city}必吃的{topic_name}！本地人推荐版！

🍜 关于{topic_name}
{landmarks_str}都是本地人常去的店，味道正宗，性价比超高！

💰 人均消费
大概在30-80元之间，丰俭由人，学生党也能吃得起。

⏰ 营业时间
大部分店铺10:00-22:00营业，有些老字号可能下午会休息。

🚇 交通指南
基本都在市中心商圈附近，地铁公交都很方便。

💡 点餐建议
1. 招牌菜必点，一般不会踩雷
2. 可以让老板推荐，他们最懂
3. 注意辣度，不能吃辣记得提前说

⚠️ 注意事项
1. 饭点人多要排队，可以错峰去
2. 有些老店只收现金，记得带现金
3. 卫生条件参差不齐，肠胃不好慎重

💡 实用Tips：
1. 关注店铺公众号，有时候有优惠券
2. 可以打包带走，味道不会差
3. 多问问本地人，他们的推荐最靠谱"""
        tags = [f"{city}美食", f"{topic_name}", "美食攻略", "本地人推荐"]
        
    elif topic_type == 'hotel':
        # 住宿类攻略
        content = f"""来{city}住哪里？超全住宿攻略来了！

🏨 关于{topic_name}
{landmarks_str}这些区域都是热门住宿地，交通方便，配套齐全。

💰 价格区间
经济型100-300元，舒适型300-600元，高端型600+，按需选择。

📍 位置选择
市中心交通便利但贵，郊区便宜但要多花时间在路上。

🚇 交通配套
优先选择地铁站附近的，出行方便，晚上回来也安全。

💡 预订建议
1. 提前3-7天预订，价格更优惠
2. 看评价要看差评，更真实
3. 节假日要提前更久，不然没房

⚠️ 注意事项
1. 确认是否含早餐，早餐质量如何
2. 看清楚退改政策，避免损失
3. 到店先检查房间设施

💡 实用Tips：
1. 加入酒店会员，积分可以换房
2. 工作日比周末便宜很多
3. 多平台比价，价格差异挺大的"""
        tags = [f"{city}住宿", f"{topic_name}", "酒店攻略", "住宿推荐"]
        
    elif topic_type == 'activity':
        # 活动/体验类攻略
        content = f"""来{city}玩什么？{topic_name}体验攻略！

🎯 关于{topic_name}
{landmarks_str}这些都是当地特色体验，来了一定要试试！

💰 费用预算
根据项目不同，大概在50-300元之间，物有所值。

⏰ 最佳时间
建议提前预约，周末和节假日人会比较多。

🚇 如何到达
大部分都在景区或商圈附近，交通很方便。

💡 体验建议
1. 穿舒适的衣服和鞋子
2. 听从工作人员指导，注意安全
3. 可以拍照留念，记录美好时刻

⚠️ 注意事项
1. 看清楚项目要求和限制
2. 保管好随身物品
3. 注意天气情况，有些项目受天气影响

💡 实用Tips：
1. 团购平台有优惠，可以省不少钱
2. 工作日人少体验更好
3. 带上朋友一起，更有意思"""
        tags = [f"{city}玩乐", f"{topic_name}", "体验攻略", "必玩项目"]
        
    else:
        # 景点类攻略（默认）
        content = f"""来{city}必打卡的{topic_name}！超详细攻略来了！

📍 关于{topic_name}
{landmarks_str}都是{city}的标志性景点，来了一定要去看看！

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
3. 尝试当地特色美食，不要只吃连锁店"""
        tags = [f"{city}旅游", f"{city}攻略", "旅游指南", "必打卡"]
    
    return {
        "title": title,
        "content": content,
        "tags": tags
    }

