"""
自定义数据库调度器 - v3 激进重置版
彻底解决 enabled 0->1 和参数更新问题的终极方案
"""

import time
import hashlib
from datetime import datetime, timedelta
from celery import schedules
from celery.beat import Scheduler, ScheduleEntry
from celery.schedules import crontab
from celery.utils.log import get_logger
from typing import Dict, Any, Optional

from ..db.database import get_scheduler_db_session
from ..db.models import ScheduledTaskModel
from .tasks import execute_plugin_task

logger = get_logger(__name__)


class DatabaseScheduleEntry(ScheduleEntry):
    """数据库调度条目 - 激进重置版"""
    
    def __init__(self, model=None, app=None, **kwargs):
        """初始化数据库调度条目"""
        
        if model is not None:
            # 方式1：从 ScheduledTaskModel 构建
            logger.debug(f"Creating new DatabaseScheduleEntry for task: {model.id}")
            
            self.model = model
            self.app = app
            self.task_id = model.id
            
            # 构建调度配置
            schedule = self._build_schedule()
            
            # 构建任务签名
            task_signature = execute_plugin_task.s(
                model.plugin_name, 
                **model.parameters
            )
            
            # 构建选项
            options = {
                'queue': 'plugin_tasks',
                'priority': model.priority,
            }
            
            if model.timeout:
                options['time_limit'] = model.timeout
                
            if model.max_retries:
                options['retry'] = True
                options['max_retries'] = model.max_retries
            
            # 🔥 激进重置：对于重新启用的任务，完全重置状态
            last_run_at = self._get_aggressive_last_run(model)
            
            super().__init__(
                name=model.id,
                task=task_signature,
                schedule=schedule,
                args=(),
                kwargs={},
                options=options,
                last_run_at=last_run_at,
                total_run_count=0,
                relative=False,
            )
            
            # 立即计算和更新 next_run
            self._force_next_run_calculation()
        else:
            # 方式2：Celery 重新创建
            logger.debug(f"Recreating DatabaseScheduleEntry from kwargs: {kwargs.get('name', 'unknown')}")
            
            entry_kwargs = kwargs.copy()
            self.model = entry_kwargs.pop('model', None)
            self.app = entry_kwargs.pop('app', app)
            self.task_id = entry_kwargs.get('name')
            
            super().__init__(**entry_kwargs)
    
    def _get_aggressive_last_run(self, model):
        """
        🔥 激进的 last_run 处理策略
        
        对于可能重新启用的任务，采用更激进的重置策略
        """
        # 如果任务从未运行过，确保立即调度
        if not model.last_run:
            logger.info(f"🚀 Task {model.id} never ran - forcing immediate scheduling")
            return None
        
        # 检查是否是最近更新的任务（可能是重新启用或参数修改）
        if model.updated_at and model.last_run:
            time_gap = (model.updated_at - model.last_run).total_seconds()
            
            # 🔥 更激进的时间阈值：30分钟内的任何更新都认为需要重置
            if time_gap > 1800:  # 30分钟
                logger.warning(f"🔄 Task {model.id} updated {time_gap}s after last run - AGGRESSIVE RESET")
                # 强制重置数据库中的 last_run
                self._force_reset_database_last_run(model.id)
                return None
            
            # 即使时间间隔不大，如果是刚刚更新的，也重置
            if time_gap > 60:  # 1分钟
                logger.warning(f"⚡ Task {model.id} recently updated - SOFT RESET")
                return None
        
        return model.last_run
    
    def _force_reset_database_last_run(self, task_id):
        """强制重置数据库中的 last_run"""
        try:
            with get_scheduler_db_session() as session:
                db_task = session.get(ScheduledTaskModel, task_id)
                if db_task:
                    db_task.last_run = None
                    db_task.next_run = None
                    session.add(db_task)
                    session.commit()
                    logger.warning(f"🔥 FORCED database reset for task: {task_id}")
        except Exception as e:
            logger.error(f"Failed to force reset database for task {task_id}: {e}")
    
    def _force_next_run_calculation(self):
        """强制计算并更新 next_run 时间"""
        if not self.model:
            return
            
        try:
            # 立即计算下次运行时间
            is_due_result = self.schedule.is_due(self.last_run_at)
            
            if hasattr(is_due_result, 'next') and is_due_result.next is not None:
                next_run_time = datetime.now() + timedelta(seconds=is_due_result.next)
                
                # 更新数据库
                with get_scheduler_db_session() as session:
                    db_task = session.get(ScheduledTaskModel, self.model.id)
                    if db_task:
                        db_task.next_run = next_run_time
                        session.add(db_task)
                        session.commit()
                        logger.info(f"⏰ Calculated next_run for {self.model.id}: {next_run_time}")
            else:
                logger.warning(f"⚠️ Could not calculate next_run for {self.model.id}")
                        
        except Exception as e:
            logger.error(f"Failed to calculate next_run for task {self.model.id}: {e}")
    
    def _build_schedule(self):
        """构建调度配置"""
        if not self.model:
            logger.error("Cannot build schedule without model")
            return schedules.schedule(run_every=timedelta(hours=1))
            
        if self.model.schedule_type == "interval":
            interval = self.model.schedule_config.get("interval", 3600)
            return schedules.schedule(run_every=timedelta(seconds=interval))
        
        elif self.model.schedule_type == "cron":
            cron_expr = self.model.schedule_config.get("cron", "0 * * * *")
            parts = cron_expr.split()
            
            if len(parts) != 5:
                logger.error(f"Invalid cron expression: {cron_expr}")
                return schedules.schedule(run_every=timedelta(hours=1))
            
            try:
                return crontab(
                    minute=parts[0],
                    hour=parts[1], 
                    day_of_month=parts[2],
                    month_of_year=parts[3],
                    day_of_week=parts[4]
                )
            except Exception as e:
                logger.error(f"Failed to parse cron expression {cron_expr}: {e}")
                return schedules.schedule(run_every=timedelta(hours=1))
        
        else:
            logger.error(f"Unsupported schedule type: {self.model.schedule_type}")
            return schedules.schedule(run_every=timedelta(hours=1))
    
    def is_due(self):
        """检查任务是否到期 - 强制启用检查"""
        # 直接检查数据库状态（绕过缓存）
        if self.model:
            try:
                with get_scheduler_db_session() as session:
                    fresh_task = session.get(ScheduledTaskModel, self.model.id)
                    if fresh_task and not fresh_task.enabled:
                        return schedules.schedstate(False, None)
            except Exception as e:
                logger.error(f"Failed to check enabled status for {self.model.id}: {e}")
        
        return self.schedule.is_due(self.last_run_at)
    
    def __next__(self):
        """执行任务并更新状态 - 激进更新版"""
        # 获取下一次调度结果
        next_entry = super().__next__()
        
        # 🔥 激进更新数据库状态
        try:
            task_id = (
                self.model.id if self.model else 
                getattr(self, 'task_id', None) or 
                self.name
            )
            
            if task_id:
                with get_scheduler_db_session() as session:
                    db_task = session.get(ScheduledTaskModel, task_id)
                    if db_task:
                        now = datetime.now()
                        
                        # 🔥 强制更新所有时间字段
                        db_task.last_run = now
                        db_task.updated_at = now
                        
                        # 重新计算 next_run
                        try:
                            schedule_obj = self._build_schedule() if self.model else self.schedule
                            is_due_result = schedule_obj.is_due(now)
                            
                            if hasattr(is_due_result, 'next') and is_due_result.next:
                                db_task.next_run = now + timedelta(seconds=is_due_result.next)
                                logger.info(f"🔄 Aggressive update - next_run: {db_task.next_run}")
                            
                        except Exception as e:
                            logger.error(f"Failed to calculate next_run for {task_id}: {e}")
                        
                        session.add(db_task)
                        session.commit()
                        logger.info(f"🔥 AGGRESSIVE execution update for task: {task_id}")
                        
        except Exception as e:
            logger.error(f"Failed to aggressively update task execution: {e}")
        
        return next_entry


class DatabaseScheduler(Scheduler):
    """
    🔥 激进重置数据库调度器 v3
    
    彻底解决 enabled 0->1 和参数更新问题的终极方案：
    - 强制堆重建
    - 激进状态重置  
    - 绕过 Celery 缓存
    - 底层调度器重启
    """
    
    Entry = DatabaseScheduleEntry
    DEFAULT_MAX_INTERVAL = 5  # seconds
    
    def __init__(self, *args, **kwargs):
        # 🔥 初始化标志 - 防止初始化期间触发激进重置
        self._in_initialization = True
        
        self._schedule = None
        self._last_timestamp = None
        self._last_task_count = None
        self._last_task_signature = None
        self._last_content_hash = None
        self._last_enabled_timestamp = None
        self._last_enabled_map = {}  # 跟踪 enabled 状态变化
        self._initial_read = True
        self._heap_invalidated = False
        
        # 🔥 激进重置计数器
        self._aggressive_reset_count = 0
        self._last_aggressive_reset = None
        
        self.app = kwargs.get('app')
        
        self.max_interval = (
            kwargs.get('max_interval') or
            (self.app.conf.get('beat_max_loop_interval') if self.app else None) or  
            self.DEFAULT_MAX_INTERVAL
        )
        
        super().__init__(*args, **kwargs)
        
        # 🔥 初始化完成
        self._in_initialization = False
        logger.info(f"🔥 DatabaseScheduler v3 (AGGRESSIVE) initialized with max_interval={self.max_interval}s")
    
    def setup_schedule(self):
        """设置调度表 - 激进版"""
        logger.info("🔥 Setting up AGGRESSIVE database schedule...")
        self.sync()
    
    @property
    def schedule(self):
        """
        🔥 激进的调度表管理
        
        强制检测变化并完全重建调度状态
        """
        update = False
        
        if self._initial_read:
            logger.info("🚀 Initial schedule read")
            update = True
            self._initial_read = False
        elif self._is_scheduler_ready() and self.schedule_changed():
            logger.warning("🔥 AGGRESSIVE schedule change detected - forcing complete rebuild")
            update = True
            self._force_aggressive_reset()
        
        if update:
            logger.warning("🔄 Rebuilding schedule with AGGRESSIVE reset")
            self._schedule = self.all_as_schedule()
            
            # 🔥 强制失效调度堆
            self._heap_invalidated = True
            
            # 🔥 直接重建堆（仅在调度器完全初始化后）
            if self._is_scheduler_ready():
                self._force_heap_rebuild()
            else:
                logger.debug("🔥 Scheduler not ready, deferring heap rebuild")
        
        return self._schedule or {}
    
    def _is_scheduler_ready(self):
        """检查调度器是否已完全初始化"""
        # 检查 Celery Beat 的核心组件是否已初始化
        return (
            hasattr(self, 'app') and self.app is not None and
            hasattr(self, 'populate_heap') and 
            not getattr(self, '_in_initialization', False)
        )
    
    def _force_aggressive_reset(self):
        """🔥 强制激进重置"""
        self._aggressive_reset_count += 1
        self._last_aggressive_reset = datetime.now()
        
        logger.warning(f"🔥 AGGRESSIVE RESET #{self._aggressive_reset_count}")
        
        # 重置所有缓存状态
        self._schedule = None
        self._last_timestamp = None
        self._last_task_count = None
        self._last_task_signature = None
        self._last_content_hash = None
        self._last_enabled_timestamp = None
        self._last_enabled_map = {}
        
        # 🔥 强制重置堆 - 安全检查
        self._heap_invalidated = True
        if hasattr(self, '_heap') and self._heap is not None:
            try:
                self._heap.clear()
                logger.debug(f"🔥 Heap cleared ({len(self._heap)} entries)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clear heap: {e}")
        else:
            logger.debug("🔥 Heap not yet initialized, marking for invalidation")
        
    def _force_heap_rebuild(self):
        """🔥 强制重建调度堆"""
        try:
            # 🔥 安全检查：确保堆已初始化
            if hasattr(self, '_heap') and self._heap is not None:
                logger.warning(f"🔥 Clearing existing heap with {len(self._heap)} entries")
                self._heap.clear()
            else:
                logger.debug("🔥 Heap not yet initialized, will be built on first populate")
            
            # 🔥 强制重新填充堆（如果调度器已初始化）
            if hasattr(self, 'populate_heap'):
                self.populate_heap()
                heap_size = len(getattr(self, '_heap', []))
                logger.warning(f"🔥 Heap forcibly rebuilt with {heap_size} entries")
            else:
                logger.debug("🔥 Scheduler not fully initialized, deferring heap population")
            
        except Exception as e:
            logger.error(f"Failed to force heap rebuild: {e}")
            # 继续执行，不让堆重建失败影响整个调度器
    
    def schedule_changed(self):
        """
        🔥 激进的变化检测机制
        
        多层检测确保没有变化被遗漏
        """
        # 🔥 如果调度器还在初始化中，跳过变化检测
        if getattr(self, '_in_initialization', True):
            logger.debug("🔥 Scheduler in initialization, skipping change detection")
            return False
            
        try:
            with get_scheduler_db_session() as session:
                # 获取所有启用的任务
                enabled_tasks = session.query(ScheduledTaskModel).filter(
                    ScheduledTaskModel.enabled == True
                ).all()
                
                # 🔥 5层检测机制
                
                # 1. 任务数量变化检测
                current_count = len(enabled_tasks)
                if self._last_task_count != current_count:
                    logger.warning(f"🔥 Task count changed: {self._last_task_count} -> {current_count}")
                    self._last_task_count = current_count
                    return True
                
                # 2. 任务列表签名变化检测
                current_signature = self._calculate_task_signature(enabled_tasks)
                if self._last_task_signature != current_signature:
                    logger.warning(f"🔥 Task signature changed: {self._last_task_signature} -> {current_signature}")
                    self._last_task_signature = current_signature
                    return True
                
                # 3. 🔥 激进的内容哈希检测
                current_content_hash = self._calculate_aggressive_content_hash(enabled_tasks)
                if self._last_content_hash != current_content_hash:
                    logger.warning(f"🔥 Content hash changed: {self._last_content_hash[:8]}... -> {current_content_hash[:8]}...")
                    self._last_content_hash = current_content_hash
                    return True
                
                # 4. 🔥 Enabled 状态变化专项检测
                if self._check_enabled_state_changes(enabled_tasks):
                    logger.warning("🔥 Enabled state changes detected")
                    return True
                
                # 5. 🔥 时间戳变化检测（精确到秒）
                if enabled_tasks:
                    from sqlalchemy import func
                    latest_update = session.query(func.max(ScheduledTaskModel.updated_at)).filter(
                        ScheduledTaskModel.enabled == True
                    ).scalar()
                    
                    if latest_update and self._last_enabled_timestamp:
                        if latest_update > self._last_enabled_timestamp:
                            time_diff = (latest_update - self._last_enabled_timestamp).total_seconds()
                            logger.warning(f"🔥 Enabled tasks timestamp changed: +{time_diff}s")
                            self._last_enabled_timestamp = latest_update
                            return True
                    elif latest_update:
                        self._last_enabled_timestamp = latest_update
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking schedule changes: {e}")
            return True  # 出错时强制重新加载
    
    def _calculate_aggressive_content_hash(self, tasks):
        """🔥 激进的内容哈希计算"""
        content_parts = []
        
        for task in sorted(tasks, key=lambda t: t.id):
            # 包含几乎所有可能影响调度的字段
            task_content = {
                'id': task.id,
                'name': task.name,
                'plugin_name': task.plugin_name,
                'parameters': task.parameters,
                'schedule_type': task.schedule_type,
                'schedule_config': task.schedule_config,
                'enabled': task.enabled,
                'priority': task.priority,
                'max_retries': task.max_retries,
                'timeout': task.timeout,
                'description': task.description,
                'tags': task.tags,
                # 🔥 包含时间戳确保检测到任何更新
                'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'next_run': task.next_run.isoformat() if task.next_run else None,
            }
            content_parts.append(str(sorted(task_content.items())))
        
        content_string = '|'.join(content_parts)
        return hashlib.md5(content_string.encode()).hexdigest()
    
    def _calculate_task_signature(self, tasks):
        """计算任务列表签名"""
        if not tasks:
            return "empty"
        
        # 使用任务ID和启用状态创建签名
        task_items = [(t.id, t.enabled) for t in sorted(tasks, key=lambda x: x.id)]
        signature_string = str(task_items)
        return hashlib.md5(signature_string.encode()).hexdigest()
    
    def _check_enabled_state_changes(self, current_tasks):
        """🔥 专项检测 enabled 状态变化"""
        current_enabled_map = {task.id: task.enabled for task in current_tasks}
        
        # 检查所有数据库中的任务（包括禁用的）
        try:
            with get_scheduler_db_session() as session:
                all_tasks = session.query(ScheduledTaskModel).all()
                full_enabled_map = {task.id: task.enabled for task in all_tasks}
                
                # 检测状态变化
                for task_id, enabled in full_enabled_map.items():
                    last_enabled = self._last_enabled_map.get(task_id)
                    if last_enabled is not None and last_enabled != enabled:
                        if enabled:
                            logger.warning(f"🔄 Task re-enabled: {task_id} (0->1)")
                            # 🔥 立即重置该任务的状态
                            self._force_task_state_reset(task_id)
                        else:
                            logger.warning(f"⏸️  Task disabled: {task_id} (1->0)")
                        
                        # 更新状态映射
                        self._last_enabled_map[task_id] = enabled
                        return True
                
                # 更新完整的状态映射
                self._last_enabled_map = full_enabled_map
                
        except Exception as e:
            logger.error(f"Failed to check enabled state changes: {e}")
        
        return False
    
    def _force_task_state_reset(self, task_id):
        """🔥 强制重置单个任务状态"""
        try:
            with get_scheduler_db_session() as session:
                task = session.get(ScheduledTaskModel, task_id)
                if task and task.enabled:
                    # 🔥 激进重置
                    task.last_run = None
                    task.next_run = None
                    task.updated_at = datetime.now()
                    session.add(task)
                    session.commit()
                    logger.warning(f"🔥 FORCE RESET task state: {task_id}")
                    
        except Exception as e:
            logger.error(f"Failed to force reset task {task_id}: {e}")
    
    def all_as_schedule(self):
        """🔥 激进的调度表构建"""
        schedule_dict = {}
        
        try:
            with get_scheduler_db_session() as session:
                enabled_tasks = session.query(ScheduledTaskModel).filter(
                    ScheduledTaskModel.enabled == True
                ).all()
                
                logger.info(f"🔥 Building AGGRESSIVE schedule from {len(enabled_tasks)} enabled tasks")
                
                for task in enabled_tasks:
                    try:
                        # 🔥 每个任务都创建全新的调度条目
                        entry = self.Entry(model=task, app=self.app)
                        schedule_dict[task.id] = entry
                        
                        logger.debug(f"✅ Added aggressive entry for task: {task.id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to create aggressive entry for task {task.id}: {e}")
                
                logger.warning(f"🔥 AGGRESSIVE schedule built: {len(schedule_dict)} entries")
                
        except Exception as e:
            logger.error(f"Failed to build aggressive schedule: {e}")
        
        return schedule_dict
    
    def sync(self):
        """🔥 激进同步方法"""
        logger.debug("🔥 Aggressive database sync triggered")
        # 强制触发调度表重建
        _ = self.schedule
        
        # 🔥 额外的激进检查
        if self._last_aggressive_reset:
            time_since_reset = (datetime.now() - self._last_aggressive_reset).total_seconds()
            if time_since_reset < 10:  # 10秒内的重置被认为是激进模式
                logger.warning(f"🔥 Recent aggressive reset ({time_since_reset:.1f}s ago) - maintaining aggressive mode") 