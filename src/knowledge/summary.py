"""
知识总结模块

提供编程知识的总结、分类和存储功能。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

# 处理直接运行和模块导入两种情况
try:
    from .storage import ObsidianStorage
    from .templates import KnowledgeTemplates
except ImportError:
    from storage import ObsidianStorage
    from templates import KnowledgeTemplates


class KnowledgeSummarizer:
    """知识总结器"""

    def __init__(self, vault_path: Optional[str] = None):
        """
        初始化总结器

        Args:
            vault_path: Obsidian vault 路径
        """
        self.storage = ObsidianStorage(vault_path)
        self._config = None

    def _get_config(self):
        """获取配置"""
        if self._config is None:
            try:
                if __name__ == "__main__" and __package__ is None:
                    from src.utils.config import get_config
                else:
                    from ..utils.config import get_config
                self._config = get_config()
            except Exception:
                self._config = None
        return self._config

    def _is_auto_save_enabled(self) -> bool:
        """检查是否启用自动保存"""
        config = self._get_config()
        if config:
            return config.get("knowledge.auto_save", True)
        return True

    def summarize_session(
        self,
        session_type: str,
        content: Dict[str, Any],
        auto_save: Optional[bool] = None
    ) -> str:
        """
        总结会话知识

        Args:
            session_type: 会话类型 (coding/bug/learning)
            content: 会话内容
            auto_save: 是否自动保存，默认从配置读取

        Returns:
            生成的知识内容（Markdown）
        """
        if auto_save is None:
            auto_save = self._is_auto_save_enabled()

        if session_type == "bug":
            return self.summarize_bug_fix(
                bug_description=content.get("description", ""),
                root_cause=content.get("root_cause", ""),
                solution=content.get("solution", ""),
                code_changes=content.get("code_changes", []),
                auto_save=auto_save
            )
        elif session_type == "pattern":
            return self.summarize_pattern(
                pattern_name=content.get("name", ""),
                description=content.get("description", ""),
                code_example=content.get("code", ""),
                use_cases=content.get("use_cases", []),
                auto_save=auto_save
            )
        else:
            # 通用编程知识
            return self.summarize_coding(
                title=content.get("title", "编程知识"),
                background=content.get("background", ""),
                core_content=content.get("content", ""),
                code_example=content.get("code", ""),
                auto_save=auto_save
            )

    def summarize_bug_fix(
        self,
        bug_description: str,
        root_cause: str,
        solution: str,
        code_changes: Optional[List[str]] = None,
        auto_save: Optional[bool] = None
    ) -> str:
        """
        总结 Bug 修复经验

        Args:
            bug_description: Bug 描述
            root_cause: 根本原因
            solution: 解决方案
            code_changes: 代码变更列表
            auto_save: 是否自动保存

        Returns:
            知识内容（Markdown）
        """
        if auto_save is None:
            auto_save = self._is_auto_save_enabled()

        content = KnowledgeTemplates.bug_fix_template(
            bug_desc=bug_description,
            root_cause=root_cause,
            solution=solution,
            code_snippets=code_changes
        )

        if auto_save:
            self.storage.save_knowledge(
                title=bug_description,
                content=content,
                category="bug"
            )

        return content

    def summarize_pattern(
        self,
        pattern_name: str,
        description: str,
        code_example: str,
        use_cases: Optional[List[str]] = None,
        pros: Optional[List[str]] = None,
        cons: Optional[List[str]] = None,
        related_patterns: Optional[List[str]] = None,
        auto_save: Optional[bool] = None
    ) -> str:
        """
        总结设计模式

        Args:
            pattern_name: 模式名称
            description: 模式描述
            code_example: 代码示例
            use_cases: 应用场景
            pros: 优点
            cons: 缺点
            related_patterns: 相关模式
            auto_save: 是否自动保存

        Returns:
            知识内容（Markdown）
        """
        if auto_save is None:
            auto_save = self._is_auto_save_enabled()

        content = KnowledgeTemplates.pattern_template(
            name=pattern_name,
            description=description,
            code=code_example,
            scenarios=use_cases,
            pros=pros,
            cons=cons,
            related_patterns=related_patterns
        )

        if auto_save:
            self.storage.save_knowledge(
                title=pattern_name,
                content=content,
                category="pattern"
            )

        return content

    def summarize_coding(
        self,
        title: str,
        background: str,
        core_content: str,
        code_example: Optional[str] = None,
        related: Optional[List[str]] = None,
        scenarios: Optional[List[str]] = None,
        category: str = "python",
        auto_save: Optional[bool] = None
    ) -> str:
        """
        总结编程知识

        Args:
            title: 知识标题
            background: 背景说明
            core_content: 核心内容
            code_example: 代码示例
            related: 相关知识
            scenarios: 应用场景
            category: 分类
            auto_save: 是否自动保存

        Returns:
            知识内容（Markdown）
        """
        if auto_save is None:
            auto_save = self._is_auto_save_enabled()

        content = KnowledgeTemplates.coding_knowledge_template(
            title=title,
            background=background,
            core_content=core_content,
            code_example=code_example,
            related=related,
            scenarios=scenarios
        )

        if auto_save:
            self.storage.save_knowledge(
                title=title,
                content=content,
                category=category
            )

        return content

    def summarize_stock_decision(
        self,
        symbol: str,
        name: str,
        decision_type: str,
        reason: str,
        result: Optional[str] = None,
        lessons: Optional[List[str]] = None,
        auto_save: Optional[bool] = None
    ) -> str:
        """
        总结股票决策

        Args:
            symbol: 股票代码
            name: 股票名称
            decision_type: 决策类型
            reason: 决策原因
            result: 结果分析
            lessons: 经验教训
            auto_save: 是否自动保存

        Returns:
            知识内容（Markdown）
        """
        if auto_save is None:
            auto_save = self._is_auto_save_enabled()

        content = KnowledgeTemplates.stock_decision_template(
            symbol=symbol,
            name=name,
            decision_type=decision_type,
            reason=reason,
            result=result,
            lessons=lessons
        )

        if auto_save:
            self.storage.save_knowledge(
                title=f"{symbol} {name} - {decision_type}决策",
                content=content,
                category="stock"
            )

        return content

    def generate_daily_summary(
        self,
        date: Optional[str] = None,
        items: Optional[List[str]] = None,
        problems: Optional[List[str]] = None,
        todo: Optional[List[str]] = None,
        auto_save: Optional[bool] = None
    ) -> str:
        """
        生成每日知识总结

        Args:
            date: 日期，默认今天
            items: 今日收获
            problems: 问题与解决
            todo: 待深入学习
            auto_save: 是否自动保存

        Returns:
            每日总结内容（Markdown）
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if auto_save is None:
            auto_save = self._is_auto_save_enabled()

        content = KnowledgeTemplates.daily_summary_template(
            date=date,
            items=items,
            problems=problems,
            todo=todo
        )

        if auto_save:
            self.storage.save_daily_summary(
                date=date,
                items=items,
                problems=problems,
                todo=todo
            )

        return content

    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索知识

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            匹配的知识列表
        """
        return self.storage.search_knowledge(query, limit)

    def list_recent_knowledge(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        列出最近的知识

        Args:
            limit: 返回数量限制

        Returns:
            知识列表
        """
        files = self.storage.list_knowledge(limit=limit)
        results = []

        for file_path in files:
            try:
                knowledge = self.storage.read_knowledge(file_path)
                results.append({
                    "path": str(file_path),
                    "name": file_path.stem,
                    "title": knowledge.get("frontmatter", {}).get("title", file_path.stem),
                    "date": knowledge.get("frontmatter", {}).get("date", ""),
                    "tags": knowledge.get("frontmatter", {}).get("tags", [])
                })
            except Exception:
                continue

        return results

    def get_knowledge_by_tag(self, tag: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        按标签获取知识

        Args:
            tag: 标签
            limit: 返回数量限制

        Returns:
            知识列表
        """
        files = self.storage.list_knowledge(tag=tag, limit=limit)
        results = []

        for file_path in files:
            try:
                knowledge = self.storage.read_knowledge(file_path)
                results.append({
                    "path": str(file_path),
                    "name": file_path.stem,
                    "title": knowledge.get("frontmatter", {}).get("title", file_path.stem),
                    "content": knowledge.get("content", "")[:200] + "..."
                })
            except Exception:
                continue

        return results


def get_summarizer(vault_path: Optional[str] = None) -> KnowledgeSummarizer:
    """
    获取总结器实例

    Args:
        vault_path: vault 路径

    Returns:
        KnowledgeSummarizer 实例
    """
    return KnowledgeSummarizer(vault_path)


if __name__ == "__main__":
    print("=" * 50)
    print("知识总结模块测试")
    print("=" * 50)

    try:
        summarizer = KnowledgeSummarizer()
        print(f"[OK] Vault 路径: {summarizer.storage.vault_path}")

        # 测试 Bug 修复总结
        bug_content = summarizer.summarize_bug_fix(
            bug_description="模块导入错误",
            root_cause="相对导入和绝对导入混用",
            solution="使用 __package__ 检查支持两种导入方式",
            code_changes=["if __package__ is None: from src.xxx import yyy"],
            auto_save=False
        )
        print("[OK] Bug 修复总结测试通过")

        # 测试设计模式总结
        pattern_content = summarizer.summarize_pattern(
            pattern_name="单例模式",
            description="确保一个类只有一个实例",
            code_example="class Singleton:\n    _instance = None",
            use_cases=["配置管理器", "日志记录器"],
            auto_save=False
        )
        print("[OK] 设计模式总结测试通过")

        # 测试每日总结
        daily_content = summarizer.generate_daily_summary(
            date="2026-03-18",
            items=["学习了知识模块", "实现了 Obsidian 集成"],
            problems=["模块导入问题已解决"],
            todo=["深入学习 Obsidian 插件"],
            auto_save=False
        )
        print("[OK] 每日总结测试通过")

        # 测试搜索
        results = summarizer.search_knowledge("测试", limit=5)
        print(f"[OK] 搜索测试: {len(results)} 个结果")

        print("\n" + "=" * 50)
        print("所有测试通过")
        print("=" * 50)

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        raise