"""
知识模板模块

提供各种类型的知识模板，支持 Obsidian 格式。
"""

from datetime import datetime
from typing import List, Optional


class KnowledgeTemplates:
    """知识模板生成器"""

    # 标签常量
    TAGS = {
        "coding": "#coding",
        "python": "#coding/python",
        "stock": "#coding/stock",
        "data": "#coding/data",
        "bug": "#coding/bug",
        "pattern": "#coding/pattern",
        "tool": "#coding/tool",
    }

    # 分类到标签的映射
    CATEGORY_TAGS = {
        "python": ["#coding", "#coding/python"],
        "stock": ["#coding", "#coding/stock"],
        "data": ["#coding", "#coding/data"],
        "bug": ["#coding", "#coding/bug"],
        "pattern": ["#coding", "#coding/pattern"],
        "tool": ["#coding", "#coding/tool"],
    }

    @staticmethod
    def generate_frontmatter(
        title: str,
        tags: List[str],
        source: str = "My_Stocks",
        status: str = "active",
        date: Optional[str] = None,
        project: str = ""
    ) -> str:
        """
        生成 YAML frontmatter

        Args:
            title: 知识标题
            tags: 标签列表
            source: 来源
            status: 状态 (active, archived, draft)
            date: 日期，默认今天

        Returns:
            YAML frontmatter 字符串
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        tags_str = ", ".join(tags)

        project_line = f"\nproject: {project}" if project else ""
        return f"""---
title: {title}
date: {date}
tags: [{tags_str}]
source: {source}
status: {status}{project_line}
---
"""

    @staticmethod
    def bug_fix_template(
        bug_desc: str,
        root_cause: str,
        solution: str,
        code_snippets: Optional[List[str]] = None,
        related_knowledge: Optional[List[str]] = None
    ) -> str:
        """
        Bug 修复知识模板

        Args:
            bug_desc: Bug 描述
            root_cause: 根本原因
            solution: 解决方案
            code_snippets: 代码片段列表
            related_knowledge: 相关知识链接

        Returns:
            知识内容（Markdown）
        """
        code_section = ""
        if code_snippets:
            code_section = "\n## 代码变更\n\n```python\n" + "\n\n".join(code_snippets) + "\n```\n"

        related_section = ""
        if related_knowledge:
            related_section = "\n## 相关知识\n\n" + "\n".join(f"- [[{k}]]" for k in related_knowledge) + "\n"

        return f"""# {bug_desc}

## 背景

## 问题分析

### 错误现象
{bug_desc}

### 根本原因
{root_cause}

## 解决方案

{solution}
{code_section}
## 经验总结

1.
2.
{related_section}
"""

    @staticmethod
    def pattern_template(
        name: str,
        description: str,
        code: str,
        scenarios: Optional[List[str]] = None,
        pros: Optional[List[str]] = None,
        cons: Optional[List[str]] = None,
        related_patterns: Optional[List[str]] = None
    ) -> str:
        """
        设计模式知识模板

        Args:
            name: 模式名称
            description: 模式描述
            code: 代码示例
            scenarios: 应用场景
            pros: 优点
            cons: 缺点
            related_patterns: 相关模式

        Returns:
            知识内容（Markdown）
        """
        scenarios_section = ""
        if scenarios:
            scenarios_section = "\n## 应用场景\n\n" + "\n".join(f"- {s}" for s in scenarios) + "\n"

        pros_cons = ""
        if pros or cons:
            pros_str = "\n".join(f"  - {p}" for p in pros) if pros else ""
            cons_str = "\n".join(f"  - {c}" for c in cons) if cons else ""
            pros_cons = f"""
## 优缺点

### 优点
{pros_str if pros_str else "  - "}

### 缺点
{cons_str if cons_str else "  - "}
"""

        related_section = ""
        if related_patterns:
            related_section = "\n## 相关模式\n\n" + "\n".join(f"- [[{p}]]" for p in related_patterns) + "\n"

        return f"""# {name}

## 概述
{description}

## 代码示例

```python
{code}
```
{scenarios_section}{pros_cons}{related_section}
"""

    @staticmethod
    def daily_summary_template(
        date: str,
        items: Optional[List[str]] = None,
        problems: Optional[List[str]] = None,
        todo: Optional[List[str]] = None
    ) -> str:
        """
        每日总结模板

        Args:
            date: 日期
            items: 今日收获列表
            problems: 问题与解决列表
            todo: 待深入学习列表

        Returns:
            知识内容（Markdown）
        """
        items_section = ""
        if items:
            items_section = "\n## 今日收获\n\n" + "\n".join(f"- {item}" for item in items) + "\n"

        problems_section = ""
        if problems:
            problems_section = "\n## 问题与解决\n\n" + "\n".join(f"- {p}" for p in problems) + "\n"

        todo_section = ""
        if todo:
            todo_section = "\n## 待深入学习\n\n" + "\n".join(f"- {t}" for t in todo) + "\n"

        return f"""# 每日知识总结 - {date}
{items_section}{problems_section}{todo_section}
## 明日计划

-
"""

    @staticmethod
    def stock_decision_template(
        symbol: str,
        name: str,
        decision_type: str,
        reason: str,
        result: Optional[str] = None,
        lessons: Optional[List[str]] = None
    ) -> str:
        """
        股票决策知识模板

        Args:
            symbol: 股票代码
            name: 股票名称
            decision_type: 决策类型 (买入/卖出/持有)
            reason: 决策原因
            result: 结果分析
            lessons: 经验教训

        Returns:
            知识内容（Markdown）
        """
        result_section = ""
        if result:
            result_section = f"""
## 结果分析

{result}
"""

        lessons_section = ""
        if lessons:
            lessons_section = "\n## 经验教训\n\n" + "\n".join(f"- {l}" for l in lessons) + "\n"

        return f"""# {symbol} {name} - {decision_type}决策

## 背景

## 决策依据

{reason}
{result_section}{lessons_section}
## 相关知识

- [[股票分析方法论]]
"""

    @staticmethod
    def coding_knowledge_template(
        title: str,
        background: str,
        core_content: str,
        code_example: Optional[str] = None,
        related: Optional[List[str]] = None,
        scenarios: Optional[List[str]] = None
    ) -> str:
        """
        编程知识模板

        Args:
            title: 知识标题
            background: 背景说明
            core_content: 核心内容
            code_example: 代码示例
            related: 相关知识链接
            scenarios: 应用场景

        Returns:
            知识内容（Markdown）
        """
        code_section = ""
        if code_example:
            code_section = f"""
## 示例

```python
{code_example}
```
"""

        related_section = ""
        if related:
            related_section = "\n## 相关知识\n\n" + "\n".join(f"- [[{r}]]" for r in related) + "\n"

        scenarios_section = ""
        if scenarios:
            scenarios_section = "\n## 应用场景\n\n" + "\n".join(f"- {s}" for s in scenarios) + "\n"

        return f"""# {title}

## 背景
{background}

## 核心内容
{core_content}
{code_section}{related_section}{scenarios_section}
"""

    @classmethod
    def get_tags_for_category(cls, category: str, project: str = "") -> List[str]:
        """
        获取分类对应的标签

        Args:
            category: 分类名称
            project: 项目名称

        Returns:
            标签列表
        """
        tags = cls.CATEGORY_TAGS.get(category, ["#coding"])
        if project:
            tags = [f"#coding/{project}"] + tags
        return tags


def create_knowledge_file(
    title: str,
    content: str,
    tags: List[str],
    category: str = "",
    project: str = "",
    source: str = "My_Stocks",
    status: str = "active"
) -> str:
    """
    创建完整的知识文件内容

    Args:
        title: 知识标题
        content: 知识内容（Markdown 格式）
        tags: 标签列表
        category: 分类
        project: 项目名称
        source: 来源
        status: 状态

    Returns:
        完整的知识文件内容（包含 frontmatter）
    """
    # 如果没有提供标签，使用分类默认标签
    if not tags:
        tags = KnowledgeTemplates.get_tags_for_category(category, project)

    frontmatter = KnowledgeTemplates.generate_frontmatter(
        title=title,
        tags=tags,
        source=source,
        status=status,
        project=project
    )

    return f"{frontmatter}\n{content}"


if __name__ == "__main__":
    print("=" * 50)
    print("知识模板模块测试")
    print("=" * 50)

    # 测试 Bug 修复模板
    bug_content = KnowledgeTemplates.bug_fix_template(
        bug_desc="模块导入错误",
        root_cause="相对导入和绝对导入混用",
        solution="使用 __package__ 检查支持两种导入方式",
        code_snippets=["if __name__ == '__main__' and __package__ is None:\n    from src.utils.config import get_config\nelse:\n    from ..utils.config import get_config"]
    )
    print("\n[OK] Bug 修复模板测试通过")
    print(bug_content[:200] + "...")

    # 测试设计模式模板
    pattern_content = KnowledgeTemplates.pattern_template(
        name="单例模式",
        description="确保一个类只有一个实例",
        code="class Singleton:\n    _instance = None\n    def __new__(cls):\n        if cls._instance is None:\n            cls._instance = super().__new__(cls)\n        return cls._instance",
        scenarios=["配置管理器", "日志记录器", "数据库连接池"]
    )
    print("\n[OK] 设计模式模板测试通过")
    print(pattern_content[:200] + "...")

    # 测试每日总结模板
    daily_content = KnowledgeTemplates.daily_summary_template(
        date="2026-03-18",
        items=["学习了 Python 类型提示", "实现了知识模块"],
        problems=["模块导入问题已解决"],
        todo=["深入学习 Obsidian 插件开发"]
    )
    print("\n[OK] 每日总结模板测试通过")
    print(daily_content[:200] + "...")

    print("\n" + "=" * 50)
    print("所有模板测试通过")
    print("=" * 50)