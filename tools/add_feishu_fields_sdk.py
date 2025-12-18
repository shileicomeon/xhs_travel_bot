"""
使用飞书SDK为现有表格添加字段
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(env_path)

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import lark_oapi as lark
    from lark_oapi.api.bitable.v1 import *
except ImportError:
    print("❌ 未安装 lark-oapi SDK")
    print("请运行: pip install lark-oapi")
    sys.exit(1)


def add_fields_to_table():
    """为现有表格添加字段"""
    
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    base_id = os.getenv("FEISHU_TABLE_ID")  # app_token
    table_id = os.getenv("FEISHU_TABLE_TABLE_ID")
    
    print("="*60)
    print("🔧 使用飞书SDK添加表格字段")
    print("="*60)
    print(f"\n📊 Base ID: {base_id}")
    print(f"📋 Table ID: {table_id}")
    
    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.INFO) \
        .build()
    
    # 首先获取现有字段
    print("\n🔍 获取现有字段...")
    list_request = ListAppTableFieldRequest.builder() \
        .app_token(base_id) \
        .table_id(table_id) \
        .build()
    
    list_response = client.bitable.v1.app_table_field.list(list_request)
    
    existing_fields = set()
    if list_response.success():
        for field in list_response.data.items:
            existing_fields.add(field.field_name)
        print(f"  当前字段: {', '.join(existing_fields)}")
    else:
        print(f"  ⚠️  无法获取字段列表: {list_response.msg}")
    
    # 定义需要添加的字段
    fields_to_add = [
        {
            'name': '日期',
            'type': 5,  # 日期类型
            'property': None
        },
        {
            'name': '发布时间',
            'type': 1,  # 文本
            'property': None
        },
        {
            'name': '城市',
            'type': 1,  # 文本
            'property': None
        },
        {
            'name': '模式',
            'type': 3,  # 单选
            'property': AppTableFieldProperty.builder()
                .options([
                    AppTableFieldPropertyOption.builder()
                        .name("旅游攻略")
                        .build(),
                    AppTableFieldPropertyOption.builder()
                        .name("文字卡片")
                        .build()
                ])
                .build()
        },
        {
            'name': '状态',
            'type': 3,  # 单选
            'property': AppTableFieldProperty.builder()
                .options([
                    AppTableFieldPropertyOption.builder()
                        .name("✅ 成功")
                        .build(),
                    AppTableFieldPropertyOption.builder()
                        .name("❌ 失败")
                        .build()
                ])
                .build()
        },
        {
            'name': '笔记ID',
            'type': 1,  # 文本
            'property': None
        },
        {
            'name': '耗时',
            'type': 1,  # 文本
            'property': None
        },
        {
            'name': '图片数',
            'type': 2,  # 数字
            'property': None
        },
        {
            'name': '失败原因',
            'type': 1,  # 文本
            'property': None
        }
    ]
    
    # 添加字段
    print(f"\n🔨 开始添加字段：")
    created_count = 0
    skipped_count = 0
    
    for field_config in fields_to_add:
        field_name = field_config['name']
        
        # 跳过已存在的字段
        if field_name in existing_fields:
            print(f"  ⏭️  【{field_name}】已存在，跳过")
            skipped_count += 1
            continue
        
        # 构建字段对象
        field_builder = AppTableField.builder() \
            .field_name(field_name) \
            .type(field_config['type'])
        
        if field_config['property']:
            field_builder.property(field_config['property'])
        
        # 构造请求
        request = CreateAppTableFieldRequest.builder() \
            .app_token(base_id) \
            .table_id(table_id) \
            .request_body(field_builder.build()) \
            .build()
        
        # 发起请求
        response = client.bitable.v1.app_table_field.create(request)
        
        # 处理结果
        if response.success():
            print(f"  ✅ 【{field_name}】创建成功")
            created_count += 1
        else:
            print(f"  ❌ 【{field_name}】创建失败")
            print(f"     错误码: {response.code}")
            print(f"     错误信息: {response.msg}")
            if response.raw and response.raw.content:
                try:
                    error_detail = json.loads(response.raw.content)
                    print(f"     详细信息: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
                except:
                    pass
    
    # 汇总结果
    print(f"\n{'='*60}")
    print(f"📊 操作完成")
    print(f"  ✅ 新增字段: {created_count} 个")
    print(f"  ⏭️  跳过字段: {skipped_count} 个")
    print(f"{'='*60}")
    
    # 验证最终字段列表
    print(f"\n🔍 验证最终字段列表：")
    list_response = client.bitable.v1.app_table_field.list(list_request)
    
    if list_response.success():
        fields = list_response.data.items
        print(f"  当前共有 {len(fields)} 个字段：")
        for i, field in enumerate(fields, 1):
            print(f"    {i}. {field.field_name} (类型: {field.type})")
    
    print(f"\n💡 访问表格：")
    print(f"  https://ai.feishu.cn/base/{base_id}")


if __name__ == "__main__":
    add_fields_to_table()

