"""
My Stocks 知识总结模块

提供编程知识的总结、分类和存储功能，支持 Obsidian 格式。

使用示例:
    from src.knowledge import KnowledgeSummarizer, ObsidianStorage

    # 创建总结器
    summarizer = KnowledgeSummarizer()

    # 总结 Bug 修复
    summarizer.summarize_bug_fix(
        bug_description="模块导入错误",
        root_cause="相对导入和绝对导入混用",
        solution="使用 __package__ 检查支持两种导入方式"
    )

    # 生成每日总结
    summarizer.generate_daily_summary(
        items=["学习了知识模块", "实现了 Obsidian 集成"]
    )
"""

from .storage import ObsidianStorage, get_storage
from .summary import KnowledgeSummarizer, get_summarizer
from .templates import KnowledgeTemplates, create_knowledge_file

__all__ = [
    # 存储相关
    "ObsidianStorage",
    "get_storage",
    # 总结相关
    "KnowledgeSummarizer",
    "get_summarizer",
    # 模板相关
    "KnowledgeTemplates",
    "create_knowledge_file",
]

__version__ = "1.0.0"