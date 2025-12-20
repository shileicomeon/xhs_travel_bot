"""
主调度器 V2 - 使用小红书真实内容

新流程：
1. 从小红书搜索真实内容
2. 下载并处理图片（去水印、调整尺寸）
3. 生成攻略式文案
4. 发布到小红书
5. 记录到飞书
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境变量
env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(env_path)

from src.utils.logger import logger
from src.utils.random_helper import RandomHelper
from src.steps.step0_context import generate_context
from src.steps.step1_search_xhs import search_xhs_content
from src.steps.step2_download_images import download_and_process_images
from src.steps.step3_generate_guide import generate_guide_content
from src.steps.text_card_mode import generate_text_card_content
from src.steps.step5_publish import publish_to_xhs
from src.steps.step6_logging import log_to_feishu


def check_login_before_run():
    """在运行前检查登录状态"""
    import asyncio
    from src.services.xhs_mcp_client import XhsMcpClient
    
    logger.info("="*60)
    logger.info("🔐 检查小红书登录状态...")
    logger.info("="*60)
    
    async def _check():
        client = XhsMcpClient()
        try:
            status = await client.check_login_status()
            
            if status['is_login']:
                logger.info("✅ 已登录小红书")
                return True
            else:
                logger.warning("❌ 未登录小红书")
                logger.info("正在生成登录二维码...")
                
                # 生成二维码
                qr_path = "login_qrcode.png"
                qr_result = await client.get_login_qrcode(save_path=qr_path)
                
                logger.debug(f"二维码结果: {qr_result}")
                
                # 检查图片是否保存成功
                import os
                if not os.path.exists(qr_path):
                    logger.warning("二维码图片未生成，请检查MCP服务")
                
                logger.info(f"\n二维码图片已保存到: {qr_path}")
                logger.info("如果在远程服务器上，也可以下载图片:")
                logger.info(f"  scp user@server:{qr_path} .")
                logger.info("\n扫码登录后，请重新运行此脚本")
                logger.info("="*60)
                
                return False
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            logger.warning("将继续执行，但可能会因为未登录而失败")
            return True  # 继续执行，让后续步骤处理错误
    
    return asyncio.run(_check())


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='小红书旅游博主自动发布系统 V2')
    parser.add_argument('--test', action='store_true', help='测试模式（不真正发布）')
    parser.add_argument('--city', type=str, help='指定城市（用于测试）')
    parser.add_argument('--force', action='store_true', help='强制执行（忽略时间窗口）')
    parser.add_argument('--skip-login-check', action='store_true', help='跳过登录检查')
    args = parser.parse_args()
    
    # 检查登录状态（除非明确跳过）
    if not args.skip_login_check:
        if not check_login_before_run():
            logger.error("❌ 未登录，退出执行")
            sys.exit(1)
    
    if args.test:
        logger.info("🧪 测试模式 V2")
        run_test_mode(args.city)
    else:
        # 正常模式：检查是否应该运行
        if args.force or should_run_now():
            if args.force:
                logger.info("🚀 强制执行模式")
            else:
                logger.info("✅ 到达发布时间，开始执行")
            run_normal_mode(args.city)
        else:
            logger.info("⏰ 不在发布时间窗口内，退出")


def should_run_now():
    """判断当前是否应该执行"""
    return RandomHelper.should_run_now("08:00", "10:00")


def run_normal_mode(city=None):
    """正常模式：完整流程（支持双模式）"""
    import random
    
    # 随机决定使用哪种模式：80% 旅游攻略，20% 文字卡片
    mode = 'travel' if random.random() < 0.8 else 'text_card'
    
    logger.info("="*60)
    logger.info("🚀 小红书自动发布系统 V2（双模式）")
    logger.info(f"📅 日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🎲 模式选择: {'模式1-旅游攻略(80%)' if mode == 'travel' else '模式2-文字卡片(20%)'}")
    logger.info("="*60)
    
    if mode == 'text_card':
        # 模式2：文字卡片模式
        return run_text_card_mode()
    
    # 模式1：旅游攻略模式
    ctx = None
    result = {
        'status': 'unknown',
        'error': None
    }
    downloader = None
    current_step = "初始化"
    
    start_time = datetime.now()
    
    try:
        # Step 0: 生成上下文
        current_step = "Step 0: 生成上下文"
        logger.info(f"\n▶️  {current_step}")
        ctx = generate_context(city=city)
        logger.info(f"   城市: {ctx['city']}")
        
        # Step 1: 从小红书搜索内容
        current_step = "Step 1: 搜索小红书内容"
        logger.info(f"\n▶️  {current_step}")
        xhs_data = search_xhs_content(ctx)
        
        # Step 2: 下载并处理图片
        current_step = "Step 2: 下载并处理图片"
        logger.info(f"\n▶️  {current_step}")
        image_data = download_and_process_images(xhs_data)
        downloader = image_data['downloader']
        
        # Step 3: 生成攻略式文案
        current_step = "Step 3: AI生成攻略文案"
        logger.info(f"\n▶️  {current_step}")
        content = generate_guide_content(ctx, xhs_data)
        
        # Step 4: 组装发布数据
        current_step = "Step 4: 组装发布数据"
        logger.info(f"\n▶️  {current_step}")
        post = {
            'title': content['title'],
            'content': content['content'],
            'tags': content['tags'],
            'images': image_data['local_images'],
            'is_local': True
        }
        
        logger.info(f"   标题: {post['title']}")
        logger.info(f"   图片: {len(post['images'])}张（本地路径）")
        logger.info(f"   标签: {len(post['tags'])}个")
        
        # Step 5: 发布到小红书
        current_step = "Step 5: MCP发布到小红书"
        logger.info(f"\n▶️  {current_step}")
        publish_result = publish_to_xhs(post)
        
        # 记录成功
        result['status'] = 'success'
        result['note_id'] = publish_result.get('note_id')
        result['publish_time'] = publish_result.get('publish_time')
        result['title'] = post['title']  # 保存标题用于飞书通知
        
        # 计算耗时
        duration = (datetime.now() - start_time).total_seconds()
        result['duration'] = f"{duration:.1f}"
        
        logger.info("\n" + "="*60)
        logger.info("✅ 发布成功")
        logger.info(f"⏱️  总耗时: {duration:.1f}秒")
        logger.info("="*60)
        
    except Exception as e:
        logger.exception(f"❌ 执行失败: {e}")
        result['status'] = 'failed'
        result['error'] = str(e)
        result['failed_step'] = current_step
        
        # 保存标题（如果已生成）
        if 'content' in locals() and content:
            result['title'] = content.get('title', f"{city}旅游攻略")
        elif 'ctx' in locals() and ctx:
            result['title'] = f"{ctx.get('city', city)}旅游攻略"
        else:
            result['title'] = "旅游攻略（未完成）"
        
        # 立即发送失败通知
        logger.info("\n⚠️  检测到执行失败，立即发送飞书通知")
        try:
            from src.services.feishu_client import FeishuClient
            feishu = FeishuClient()
            simple_ctx = ctx if ctx else {'city': city if city else '未知', 'topic': '旅游攻略'}
            feishu.send_failure_notification(
                simple_ctx, 
                e,  # 传递异常对象
                title=result.get('title'),
                step=current_step
            )
            logger.info("✅ 失败通知已发送")
        except Exception as notify_error:
            logger.error(f"❌ 发送失败通知时出错: {notify_error}")
    
    finally:
        # 清理临时文件
        if downloader:
            try:
                downloader.cleanup()
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
        
        # Step 6: 记录到飞书
        if ctx:
            logger.info("\n▶️  Step 6: 记录到飞书")
            try:
                log_to_feishu(ctx, result)
                logger.info("✅ 飞书记录完成")
            except Exception as e:
                logger.error(f"❌ 飞书记录失败: {e}")


def run_test_mode(city=None):
    """测试模式：快速验证流程"""
    logger.info("="*60)
    logger.info("🧪 测试模式 V2 - 使用小红书真实内容")
    logger.info("="*60)
    
    downloader = None
    
    try:
        # Step 0: 生成上下文
        ctx = generate_context(city=city)
        logger.info(f"\n📋 城市: {ctx['city']}")
        
        # Step 1: 从小红书搜索
        logger.info(f"\n▶️  Step 1: 从小红书搜索内容")
        xhs_data = search_xhs_content(ctx)
        logger.info(f"   找到 {len(xhs_data['images'])} 张图片")
        logger.info(f"   参考标题: {xhs_data.get('reference_title', 'N/A')[:50]}")
        
        # Step 2: 下载图片
        logger.info(f"\n▶️  Step 2: 下载并处理图片")
        image_data = download_and_process_images(xhs_data)
        downloader = image_data['downloader']
        logger.info(f"   成功处理 {len(image_data['local_images'])} 张图片")
        
        # Step 3: 生成文案
        logger.info(f"\n▶️  Step 3: 生成攻略式文案")
        content = generate_guide_content(ctx, xhs_data)
        logger.info(f"\n✍️  文案:")
        logger.info(f"  标题: {content['title']}")
        logger.info(f"  正文:\n{content['content'][:300]}...")
        logger.info(f"  标签: {', '.join(content['tags'])}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ 测试完成（未实际发布）")
        logger.info("="*60)
        
    except Exception as e:
        logger.exception(f"❌ 测试失败: {e}")
        sys.exit(1)
    
    finally:
        # 清理临时文件
        if downloader:
            try:
                downloader.cleanup()
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")


def run_text_card_mode():
    """文字卡片模式：生成纯色背景+一句话内容"""
    result = {
        'status': 'unknown',
        'error': None
    }
    generator = None
    current_step = "初始化"
    
    start_time = datetime.now()
    
    try:
        # 生成文字卡片内容
        current_step = "生成文字卡片内容"
        card_data = generate_text_card_content()
        generator = card_data.get('generator')
        
        # 组装发布数据
        current_step = "组装发布数据"
        logger.info(f"\n▶️  {current_step}")
        post = {
            'title': card_data['title'],
            'content': card_data['content'],
            'tags': card_data['tags'],
            'images': [card_data['image']],  # 只有一张图
            'is_local': True
        }
        
        logger.info(f"   标题: {post['title']}")
        logger.info(f"   图片: 1张")
        logger.info(f"   标签: {len(post['tags'])}个")
        
        # 发布到小红书
        current_step = "MCP发布到小红书"
        logger.info(f"\n▶️  {current_step}")
        publish_result = publish_to_xhs(post)
        
        # 记录成功
        result['status'] = 'success'
        result['note_id'] = publish_result.get('note_id')
        result['publish_time'] = publish_result.get('publish_time')
        result['title'] = post['title']
        
        # 计算耗时
        duration = (datetime.now() - start_time).total_seconds()
        result['duration'] = f"{duration:.1f}"
        
        logger.info("\n" + "="*60)
        logger.info("✅ 发布成功（文字卡片模式）")
        logger.info(f"⏱️  总耗时: {duration:.1f}秒")
        logger.info("="*60)
        
    except Exception as e:
        logger.exception(f"❌ 执行失败: {e}")
        result['status'] = 'failed'
        result['error'] = str(e)
        result['failed_step'] = current_step
        
        # 保存标题（如果已生成）
        if 'card_data' in locals() and card_data:
            result['title'] = card_data.get('title', '文字卡片')
        else:
            result['title'] = '文字卡片（未完成）'
        
        # 立即发送失败通知
        logger.info("\n⚠️  检测到执行失败，立即发送飞书通知")
        try:
            from src.services.feishu_client import FeishuClient
            feishu = FeishuClient()
            simple_ctx = {'city': '文字卡片', 'topic': '日常分享'}
            feishu.send_failure_notification(
                simple_ctx, 
                e,  # 传递异常对象
                title=result.get('title'),
                step=current_step
            )
            logger.info("✅ 失败通知已发送")
        except Exception as notify_error:
            logger.error(f"❌ 发送失败通知时出错: {notify_error}")
    
    finally:
        # 清理临时文件
        if generator:
            try:
                generator.cleanup()
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
        
        # 记录到飞书（使用简单的ctx）
        logger.info("\n▶️  记录到飞书")
        try:
            ctx = {'city': '文字卡片', 'topic': '日常分享'}
            log_to_feishu(ctx, result)
            logger.info("✅ 飞书记录完成")
        except Exception as e:
            logger.error(f"❌ 飞书记录失败: {e}")
    
    return result


if __name__ == "__main__":
    main()

