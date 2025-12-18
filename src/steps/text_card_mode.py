"""
文字卡片模式

生成纯色背景+一句话+表情的简洁内容
"""

import os
import random
import yaml
from ..utils.logger import logger
from ..utils.text_card_generator import TextCardGenerator


def generate_text_card_content():
    """
    生成文字卡片内容（模式2）
    
    Returns:
        {
            'mode': 'text_card',
            'image': '图片路径',
            'title': '标题',
            'content': '正文',
            'tags': ['标签列表'],
            'generator': TextCardGenerator实例（用于清理）
        }
    """
    logger.info("📝 模式2: 文字卡片模式")
    
    # 加载话题库
    topics_file = "config/text_topics.yaml"
    try:
        with open(topics_file, 'r', encoding='utf-8') as f:
            topics_data = yaml.safe_load(f)
            topics = topics_data.get('topics', [])
    except Exception as e:
        logger.error(f"加载话题库失败: {e}")
        raise ValueError("无法加载话题库")
    
    if not topics:
        raise ValueError("话题库为空")
    
    # 随机选择一个话题
    topic = random.choice(topics)
    
    text = topic.get('text', '')
    emoji = topic.get('emoji', '')
    tags = topic.get('tags', [])
    
    logger.info(f"  选中话题: {emoji} {text}")
    logger.info(f"  标签: {', '.join(tags)}")
    
    # 生成文字卡片图片
    generator = TextCardGenerator()
    image_path = generator.generate_card(
        text=text,
        emoji=emoji,
        filename="text_card_01.jpg"
    )
    
    # 生成标题（就是话题文字本身）
    title = f"{emoji}{text}" if emoji else text
    
    # 生成正文（扩展一下，但保持简洁）
    content = _generate_simple_content(text, emoji)
    
    logger.info(f"✅ 文字卡片内容生成完成")
    logger.info(f"   标题: {title}")
    logger.info(f"   图片: {image_path}")
    
    return {
        'mode': 'text_card',
        'image': image_path,
        'title': title,
        'content': content,
        'tags': tags,
        'generator': generator,
        'is_local': True
    }


def _generate_simple_content(text, emoji):
    """
    生成简洁的正文内容
    
    根据话题类型生成不同的正文
    """
    # 根据关键词判断类型
    if any(keyword in text for keyword in ['上班', '辞职', '打工', '周五', '卑微']):
        # 职场类
        contents = [
            f"{emoji}{text}\n\n每个打工人都不容易，但我们都在努力生活着。\n\n今天也要加油鸭！💪",
            f"{emoji}{text}\n\n生活不易，但总要继续前行。\n\n愿我们都能找到属于自己的节奏。🌟",
            f"{emoji}{text}\n\n谁的人生不是一边崩溃一边自愈呢？\n\n明天又是全新的一天！✨",
        ]
    elif any(keyword in text for keyword in ['逃离', '治愈', '走走', '厌倦']):
        # 逃离城市类
        contents = [
            f"{emoji}{text}\n\n有时候真的需要暂时离开，去看看不一样的风景。\n\n给自己一点空间，给心灵一次放松。🌿",
            f"{emoji}{text}\n\n生活不止眼前的苟且，还有诗和远方。\n\n偶尔出逃，是为了更好地回来。🎒",
            f"{emoji}{text}\n\n城市虽繁华，但有时也需要一场说走就走的旅行。\n\n去治愈，去放空，去重新找回自己。💫",
        ]
    elif any(keyword in text for keyword in ['快乐', '值得', '美好', '仪式感']):
        # 生活感悟类
        contents = [
            f"{emoji}{text}\n\n生活需要一点小确幸，需要一点仪式感。\n\n珍惜每一个美好瞬间。💕",
            f"{emoji}{text}\n\n慢慢来，一切都来得及。\n\n温柔对待自己，热爱生活的每一天。🌸",
            f"{emoji}{text}\n\n幸福很简单，就藏在生活的点点滴滴里。\n\n保持热爱，奔赴山海。✨",
        ]
    elif any(keyword in text for keyword in ['周末', '发呆', '躺平', '摆烂', '咸鱼']):
        # 周末休闲类
        contents = [
            f"{emoji}{text}\n\n周末就该这样，慢悠悠地度过。\n\n什么都不想，什么都不做，就是最好的休息。😌",
            f"{emoji}{text}\n\n偶尔给自己放个假，彻底放松一下。\n\n充电完毕，下周再战！🔋",
            f"{emoji}{text}\n\n生活需要张弛有度，该躺平时就躺平。\n\n休息好了才能更好地出发。🛌",
        ]
    else:
        # 旅行向往类
        contents = [
            f"{emoji}{text}\n\n心之所向，身必往之。\n\n总有一天，我会去到那些梦想的地方。🗺️",
            f"{emoji}{text}\n\n世界那么大，总要去看看。\n\n把梦想写进清单，一个一个去实现。✈️",
            f"{emoji}{text}\n\n旅行的意义，在于遇见不一样的自己。\n\n勇敢出发吧！🎒",
        ]
    
    return random.choice(contents)

