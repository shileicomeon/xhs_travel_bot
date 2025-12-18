#!/usr/bin/env python3
"""
测试飞书失败通知功能

用于验证增强的错误定位和建议功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.feishu_client import FeishuClient


def test_different_error_types():
    """测试不同类型的错误通知"""
    
    feishu = FeishuClient()
    
    # 测试场景
    test_cases = [
        {
            "name": "MCP服务问题",
            "error": Exception("MCP发布失败: Session with given id not found"),
            "ctx": {"city": "杭州", "topic_name": "西湖"},
            "title": "杭州西湖旅游攻略",
            "step": "Step 5: MCP发布到小红书"
        },
        {
            "name": "网络超时",
            "error": TimeoutError("Request timeout after 30 seconds"),
            "ctx": {"city": "北京", "topic_name": "故宫"},
            "title": "北京故宫旅游攻略",
            "step": "Step 2: 下载并处理图片"
        },
        {
            "name": "AI服务错误",
            "error": Exception("DeepSeek API error: insufficient_quota"),
            "ctx": {"city": "上海", "topic_name": "外滩"},
            "title": "上海外滩旅游攻略",
            "step": "Step 3: AI生成攻略文案"
        },
        {
            "name": "图片处理错误",
            "error": Exception("Image download failed: 404 Not Found"),
            "ctx": {"city": "成都", "topic_name": "火锅"},
            "title": "成都火锅美食攻略",
            "step": "Step 2: 下载并处理图片"
        },
        {
            "name": "权限错误",
            "error": PermissionError("Access denied: bitable:app permission required"),
            "ctx": {"city": "广州", "topic_name": "早茶"},
            "title": "广州早茶美食攻略",
            "step": "Step 6: 记录到飞书"
        },
    ]
    
    print("=" * 70)
    print("🧪 测试飞书失败通知功能")
    print("=" * 70)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}/{len(test_cases)}: {test_case['name']}")
        print("-" * 70)
        
        try:
            feishu.send_failure_notification(
                ctx=test_case['ctx'],
                error=test_case['error'],
                title=test_case['title'],
                step=test_case['step']
            )
            print("✅ 通知发送成功")
        except Exception as e:
            print(f"❌ 通知发送失败: {e}")
        
        print()
    
    print("=" * 70)
    print("✅ 测试完成")
    print("=" * 70)
    print()
    print("请检查飞书群消息，查看不同错误类型的通知效果")
    print()


if __name__ == "__main__":
    try:
        test_different_error_types()
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


