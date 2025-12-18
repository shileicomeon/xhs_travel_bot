"""
阿里通义千问客户端

用于图片分析和文案生成
"""

import os
import json
from openai import OpenAI
from ..utils.logger import logger
from ..utils.retry import retry_on_failure


class QwenClient:
    """通义千问客户端"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        if not self.api_key:
            raise ValueError("QWEN_API_KEY 未设置")
        
        # 使用OpenAI兼容接口
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        self.model_chat = "qwen-max"
        self.model_vision = "qwen-vl-max"
        self.temperature = 0.7
        self.max_tokens = 1000
    
    @retry_on_failure(max_attempts=3)
    def analyze_image(self, image_url):
        """
        分析图片内容
        
        Args:
            image_url: 图片URL
        
        Returns:
            图片描述文本
        """
        logger.debug(f"分析图片: {image_url}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_vision,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请用一句话描述这张图片的场景，突出旅游、美食、生活氛围。要求：20字以内，口语化，适合小红书风格。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                temperature=self.temperature,
                max_tokens=100
            )
            
            description = response.choices[0].message.content.strip()
            logger.debug(f"图片描述: {description}")
            
            return description
        
        except Exception as e:
            logger.error(f"图片分析失败: {e}")
            # 返回备用描述
            return "旅游场景图片"
    
    @retry_on_failure(max_attempts=3)
    def generate_content(self, city, image_descriptions):
        """
        生成小红书风格文案
        
        Args:
            city: 城市名
            image_descriptions: 图片描述列表
        
        Returns:
            {
                "title": "标题",
                "content": "正文",
                "tags": ["标签1", "标签2"]
            }
        """
        logger.info(f"生成文案: {city}")
        
        # 构建prompt
        prompt = self._build_content_prompt(city, image_descriptions)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_chat,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个小红书旅游博主，擅长写吸引人的旅游分享。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content_text = response.choices[0].message.content.strip()
            logger.debug(f"AI返回: {content_text}")
            
            # 解析JSON
            content = self._parse_content(content_text)
            
            logger.info(f"✅ 文案生成成功: {content['title']}")
            
            return content
        
        except Exception as e:
            logger.error(f"文案生成失败: {e}")
            # 返回备用文案
            return self._generate_fallback_content(city, image_descriptions)
    
    def _build_content_prompt(self, city, image_descriptions):
        """构建文案生成prompt"""
        
        # 格式化图片描述
        desc_text = ""
        type_names = {
            "city_view": "城市全景",
            "play": "景点",
            "eat": "美食",
            "drink": "饮品",
            "life": "生活",
            "extra": "补充"
        }
        
        for i, desc_item in enumerate(image_descriptions, 1):
            img_type = desc_item.get("type", "")
            desc = desc_item.get("desc", "")
            type_name = type_names.get(img_type, img_type)
            desc_text += f"图片{i}({type_name}): {desc}\n"
        
        prompt = f"""你是一个小红书旅游博主，今天在{city}体验了吃喝玩乐。
根据以下图片描述，生成一篇真实的旅游分享：

{desc_text}

要求：
1. 标题：15-20字，吸引人，不要用标点符号结尾
2. 正文：200-300字，分段，使用emoji，按图片顺序写，像真实经历
3. 标签：4-6个，包含城市、主题、热门话题，每个标签以#开头
4. 口语化，不要太正式，要有烟火气

输出JSON格式：
{{
    "title": "标题文本",
    "content": "正文内容",
    "tags": ["#标签1", "#标签2", "#标签3"]
}}

只输出JSON，不要其他内容。"""
        
        return prompt
    
    def _parse_content(self, content_text):
        """解析AI返回的内容"""
        try:
            # 尝试直接解析JSON
            content = json.loads(content_text)
            
            # 验证必需字段
            if "title" not in content or "content" not in content or "tags" not in content:
                raise ValueError("缺少必需字段")
            
            # 确保标签格式正确
            tags = content["tags"]
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            
            # 确保标签以#开头
            tags = [t if t.startswith("#") else f"#{t}" for t in tags]
            content["tags"] = tags
            
            return content
        
        except Exception as e:
            logger.warning(f"JSON解析失败: {e}，尝试提取内容")
            
            # 尝试从文本中提取
            lines = content_text.strip().split("\n")
            title = ""
            content_body = ""
            tags = []
            
            for line in lines:
                line = line.strip()
                if line.startswith("标题") or line.startswith("title"):
                    title = line.split(":", 1)[-1].strip().strip('"')
                elif line.startswith("正文") or line.startswith("content"):
                    content_body = line.split(":", 1)[-1].strip().strip('"')
                elif line.startswith("标签") or line.startswith("tags"):
                    tag_text = line.split(":", 1)[-1].strip()
                    tags = [t.strip().strip('"') for t in tag_text.split(",")]
            
            if not title or not content_body:
                raise ValueError("无法提取内容")
            
            return {
                "title": title,
                "content": content_body,
                "tags": tags
            }
    
    def _generate_fallback_content(self, city, image_descriptions):
        """生成备用文案（当AI失败时）"""
        logger.warning("使用备用文案模板")
        
        return {
            "title": f"{city}一日游攻略，吃喝玩乐全都有",
            "content": f"""早上来到{city}，城市氛围超好🏙️

📍第一站去了热门景点，人不多很舒服，随便逛逛拍拍照都很出片

🍜中午必须安排美食！找了家老店，味道真的绝了

☕下午找了家咖啡店，坐着发呆，这才是旅行的意义

🚶傍晚在老街区溜达，满满的烟火气

总结：{city}真的值得慢慢逛，下次还要来！""",
            "tags": [f"#{city}旅行", "#吃喝玩乐", "#周末去哪玩", "#城市攻略"]
        }

