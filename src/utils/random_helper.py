"""
随机工具模块

提供基于日期的确定性随机数生成
"""

import random
import hashlib
from datetime import datetime, time
import pytz


class RandomHelper:
    """随机工具类"""
    
    @staticmethod
    def get_daily_seed(date=None):
        """
        获取当天的随机种子
        
        使用日期的MD5哈希作为种子，确保每天的随机数是确定的
        
        Args:
            date: 日期对象，默认为今天
        
        Returns:
            整数种子
        """
        if date is None:
            date = datetime.now().date()
        
        date_str = str(date)
        hash_obj = hashlib.md5(date_str.encode())
        seed = int(hash_obj.hexdigest()[:8], 16)
        
        return seed
    
    @staticmethod
    def get_random_time_in_window(start_time, end_time, date=None):
        """
        获取时间窗口内的随机时间
        
        使用当天的种子，确保每天的随机时间是固定的
        
        Args:
            start_time: 开始时间字符串，如 "09:00"
            end_time: 结束时间字符串，如 "11:00"
            date: 日期对象，默认为今天
        
        Returns:
            datetime对象
        """
        if date is None:
            tz = pytz.timezone('Asia/Shanghai')
            date = datetime.now(tz).date()
        
        # 设置随机种子
        seed = RandomHelper.get_daily_seed(date)
        random.seed(seed)
        
        # 解析时间
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))
        
        # 转换为分钟数
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute
        
        # 随机选择分钟数
        random_minutes = random.randint(start_minutes, end_minutes)
        
        # 转换回时间
        hour = random_minutes // 60
        minute = random_minutes % 60
        second = random.randint(0, 59)
        
        # 创建datetime对象
        tz = pytz.timezone('Asia/Shanghai')
        random_time = datetime.combine(date, time(hour, minute, second))
        random_time = tz.localize(random_time)
        
        return random_time
    
    @staticmethod
    def should_run_now(start_time, end_time):
        """
        判断当前是否应该执行
        
        检查当前时间是否等于今天的随机时间（精确到分钟）
        
        Args:
            start_time: 开始时间字符串
            end_time: 结束时间字符串
        
        Returns:
            bool
        """
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        
        # 获取今天的随机时间
        target_time = RandomHelper.get_random_time_in_window(start_time, end_time)
        
        # 比较到分钟
        return (now.year == target_time.year and
                now.month == target_time.month and
                now.day == target_time.day and
                now.hour == target_time.hour and
                now.minute == target_time.minute)
    
    @staticmethod
    def weighted_random_choice(items, weights):
        """
        加权随机选择
        
        Args:
            items: 选项列表
            weights: 权重列表
        
        Returns:
            选中的项
        """
        return random.choices(items, weights=weights, k=1)[0]

