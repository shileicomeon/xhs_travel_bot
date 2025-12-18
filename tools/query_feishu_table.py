"""
查询飞书表格字段和记录
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


def query_table_info():
    """查询表格信息"""
    
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    base_id = os.getenv("FEISHU_TABLE_ID")  # app_token
    table_id = os.getenv("FEISHU_TABLE_TABLE_ID")
    
    print("="*60)
    print("🔍 查询飞书表格信息")
    print("="*60)
    print(f"\n📊 Base ID: {base_id}")
    print(f"📋 Table ID: {table_id}")
    
    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.INFO) \
        .build()
    
    # 1. 查询字段列表
    print("\n" + "="*60)
    print("📋 字段列表")
    print("="*60)
    
    list_field_request = ListAppTableFieldRequest.builder() \
        .app_token(base_id) \
        .table_id(table_id) \
        .page_size(100) \
        .build()
    
    list_field_response = client.bitable.v1.app_table_field.list(list_field_request)
    
    if not list_field_response.success():
        print(f"❌ 查询字段失败")
        print(f"错误码: {list_field_response.code}")
        print(f"错误信息: {list_field_response.msg}")
        return
    
    fields = list_field_response.data.items
    print(f"\n共有 {len(fields)} 个字段：\n")
    
    field_types = {
        1: "文本",
        2: "数字",
        3: "单选",
        4: "多选",
        5: "日期",
        7: "复选框",
        11: "人员",
        13: "电话号码",
        15: "超链接",
        17: "附件",
        18: "关联",
        20: "公式",
        21: "创建时间",
        22: "最后更新时间",
        23: "创建人",
        24: "修改人"
    }
    
    for i, field in enumerate(fields, 1):
        field_type_name = field_types.get(field.type, f"未知({field.type})")
        print(f"{i}. 【{field.field_name}】")
        print(f"   ID: {field.field_id}")
        print(f"   类型: {field_type_name}")
        
        # 如果是单选/多选，显示选项
        if field.type in [3, 4] and field.property and field.property.options:
            options = [opt.name for opt in field.property.options]
            print(f"   选项: {', '.join(options)}")
        
        print()
    
    # 2. 查询记录（最近10条）
    print("="*60)
    print("📝 最近的记录（最多10条）")
    print("="*60)
    
    search_request = SearchAppTableRecordRequest.builder() \
        .app_token(base_id) \
        .table_id(table_id) \
        .page_size(10) \
        .request_body(SearchAppTableRecordRequestBody.builder()
            .automatic_fields(False)
            .build()) \
        .build()
    
    search_response = client.bitable.v1.app_table_record.search(search_request)
    
    if not search_response.success():
        print(f"\n❌ 查询记录失败")
        print(f"错误码: {search_response.code}")
        print(f"错误信息: {search_response.msg}")
    else:
        records = search_response.data.items if search_response.data.items else []
        
        if len(records) == 0:
            print("\n📭 表格中暂无记录")
        else:
            print(f"\n共有 {len(records)} 条记录：\n")
            
            for i, record in enumerate(records, 1):
                print(f"记录 {i}:")
                print(f"  Record ID: {record.record_id}")
                
                if record.fields:
                    for field_name, value in record.fields.items():
                        # 简化显示值
                        if isinstance(value, list):
                            display_value = ', '.join([str(v) for v in value[:3]])
                            if len(value) > 3:
                                display_value += f" ... (共{len(value)}项)"
                        else:
                            display_value = str(value)[:100]
                        
                        print(f"  {field_name}: {display_value}")
                
                print()
    
    print("="*60)
    print("✅ 查询完成")
    print("="*60)
    
    # 检查缺少的字段
    print("\n💡 字段检查：")
    required_fields = [
        '日期', '发布时间', '标题', '城市', '模式', 
        '状态', '笔记ID', '耗时', '图片数', '失败原因'
    ]
    
    existing_field_names = {field.field_name for field in fields}
    missing_fields = [f for f in required_fields if f not in existing_field_names]
    
    if missing_fields:
        print(f"  ⚠️  缺少以下字段：{', '.join(missing_fields)}")
        print(f"  💡 运行 add_feishu_fields_sdk.py 来添加缺失的字段")
    else:
        print(f"  ✅ 所有必需字段都已存在")
    
    print(f"\n🌐 访问表格：")
    print(f"  https://ai.feishu.cn/base/{base_id}")


if __name__ == "__main__":
    query_table_info()

