# -*- coding: utf-8 -*-
"""
生成今日知识总结
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge import ObsidianStorage, KnowledgeTemplates
from datetime import datetime


def main():
    storage = ObsidianStorage()
    today = datetime.now().strftime("%Y-%m-%d")

    print("=" * 50)
    print(f"Generating daily summary: {today}")
    print("=" * 50)

    # 1. 生成每日开发总结
    daily_content = KnowledgeTemplates.daily_summary_template(
        date=today,
        items=[
            "实现了知识总结模块 (src/knowledge/)",
            "创建了 Obsidian 存储集成 (storage.py)",
            "实现了知识模板系统 (templates.py)",
            "支持 Bug 修复、设计模式、每日总结等模板",
            "更新了 config.yaml 添加知识模块配置",
            "修复了模块导入兼容性问题 (try/except ImportError)",
            "修复了文件名清理逻辑，移除 Windows 非法字符"
        ],
        problems=[
            "模块导入问题: 相对导入在直接运行时报错，使用 try/except 解决",
            "文件名问题: Windows 文件名不能包含冒号，添加了 _sanitize_filename 方法"
        ],
        todo=[
            "深入学习 Obsidian 插件开发",
            "实现技术分析模块 (src/analysis/)",
            "实现决策模块 (src/decision/)"
        ]
    )
    daily_path = storage.save_knowledge(
        title=f"每日知识总结 - {today}",
        content=daily_content,
        category="tool",
        filename=f"每日总结_{today.replace('-', '')}"
    )
    print(f"[OK] Daily summary: {daily_path}")

    # 2. 保存 Python 模块导入兼容性知识
    coding_content = KnowledgeTemplates.coding_knowledge_template(
        title="Python 模块导入兼容性处理",
        background="在开发可独立运行又可作为模块导入的 Python 文件时，需要处理两种导入方式的兼容性。",
        core_content="""使用 try/except ImportError 模式处理导入兼容性：

1. **相对导入**: 用于包内导入 (from .module import func)
2. **绝对导入**: 用于直接运行 (from module import func)

最佳实践：
- 优先使用相对导入（包内标准做法）
- 使用 try/except 捕获 ImportError 后回退到绝对导入
- 避免使用 __package__ 检查，直接用 try/except 更简洁""",
        code_example="""try:
    from .module import func  # 优先尝试相对导入
except ImportError:
    from module import func   # 回退到绝对导入""",
        related=["Python 包结构设计", "模块导入机制"],
        scenarios=["开发可独立运行的模块", "脚本工具开发", "库开发"]
    )
    coding_path = storage.save_knowledge(
        title="Python 模块导入兼容性处理",
        content=coding_content,
        category="python"
    )
    print(f"[OK] Coding knowledge: {coding_path}")

    # 3. 保存 Bug 修复经验
    bug_content = KnowledgeTemplates.bug_fix_template(
        bug_desc="Python 相对导入报错 ImportError",
        root_cause="当 Python 文件直接运行时，__package__ 为 None，此时相对导入会失败。相对导入只在模块作为包的一部分导入时才有效。",
        solution="""使用 try/except ImportError 模式：
1. 首先尝试相对导入（标准包内导入方式）
2. 如果失败则回退到绝对导入

这种方式比检查 __package__ 更简洁，且能正确处理所有情况。""",
        code_snippets=["""# Old code (problematic)
if __name__ == '__main__' and __package__ is None:
    from module import func
else:
    from .module import func

# New code (recommended)
try:
    from .module import func
except ImportError:
    from module import func"""]
    )
    bug_path = storage.save_knowledge(
        title="Python 相对导入报错 ImportError",
        content=bug_content,
        category="bug"
    )
    print(f"[OK] Bug fix: {bug_path}")

    # 4. 保存单例模式知识
    pattern_content = KnowledgeTemplates.pattern_template(
        name="Singleton Pattern",
        description="确保一个类只有一个实例，并提供一个全局访问点。常用于配置管理器、日志记录器、数据库连接池等场景。",
        code="""class ConfigManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # 初始化逻辑
        self._initialized = True""",
        scenarios=[
            "配置管理器 - 全局配置访问",
            "日志记录器 - 统一日志输出",
            "数据库连接池 - 管理连接资源"
        ],
        pros=[
            "控制实例数量，节省资源",
            "全局访问点，方便使用",
            "延迟初始化，提高性能"
        ],
        cons=[
            "可能隐藏依赖关系",
            "难以进行单元测试",
            "在多线程环境下需要额外处理"
        ]
    )
    pattern_path = storage.save_knowledge(
        title="Singleton Pattern",
        content=pattern_content,
        category="pattern"
    )
    print(f"[OK] Design pattern: {pattern_path}")

    print("=" * 50)
    print("Knowledge summary generated successfully!")
    print(f"Vault path: {storage.vault_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()