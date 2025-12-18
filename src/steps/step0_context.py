"""
Step 0: 生成上下文

为当天发布生成随机种子和内容参数
"""

import random
import yaml
from pathlib import Path
from datetime import datetime
from ..utils.logger import logger
from ..utils.random_helper import RandomHelper


def generate_context(city=None):
    """
    生成当天的上下文
    
    Args:
        city: 指定城市（用于测试），None则随机选择
    
    Returns:
        {
            "city": "成都",
            "topic": "吃喝玩乐",
            "image_count": 6,
            "seed": 83912,
            "publish_time": "09:35:42",
            "keywords": {...}
        }
    """
    logger.info("Step 0: 生成上下文")
    
    # 加载城市配置
    config_path = Path(__file__).parent.parent.parent / "config" / "cities.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    cities = config['cities']
    
    # 选择城市
    if city:
        # 指定城市（测试模式）
        city_config = next((c for c in cities if c['name'] == city), cities[0])
    else:
        # 随机选择（考虑权重）
        city_config = _select_city_with_weight(cities)
    
    # 生成随机参数
    seed = RandomHelper.get_daily_seed()
    random.seed(seed)
    
    image_count = random.randint(4, 8)
    
    # 🆕 随机选择一个具体主题
    topics = city_config.get('topics', [])
    if topics:
        selected_topic = random.choice(topics)
    else:
        # 兼容旧配置：没有topics时使用通用主题
        selected_topic = {
            'type': 'general',
            'name': '旅游攻略'
        }
    
    # 生成上下文
    ctx = {
        "city": city_config['name'],
        "topic": selected_topic,  # 🆕 完整的主题对象
        "topic_name": selected_topic['name'],  # 🆕 主题名称
        "topic_type": selected_topic['type'],  # 🆕 主题类型
        "image_count": image_count,
        "seed": seed,
        "publish_time": datetime.now().strftime("%H:%M:%S"),
        "keywords": city_config['keywords']
    }
    
    logger.info(f"✅ 上下文生成完成: {ctx['city']} - {ctx['topic_name']} ({ctx['topic_type']}), {ctx['image_count']}张图片")
    
    return ctx


def _select_city_with_weight(cities):
    """
    加权随机选择城市
    
    TODO: 从飞书表格查询最近发布记录，计算权重
    现在简化为随机选择
    """
    # 简化版：根据priority选择
    high_priority = [c for c in cities if c.get('priority') == 'high']
    medium_priority = [c for c in cities if c.get('priority') == 'medium']
    low_priority = [c for c in cities if c.get('priority') == 'low']
    
    # 权重：high=5, medium=3, low=1
    all_cities = high_priority * 5 + medium_priority * 3 + low_priority * 1
    
    return random.choice(all_cities)

