"""
Obsidian 知识存储模块

支持将知识保存到 Obsidian vault，使用 YAML frontmatter 和标签系统。
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 处理直接运行和模块导入两种情况
try:
    from .templates import KnowledgeTemplates, create_knowledge_file
except ImportError:
    from templates import KnowledgeTemplates, create_knowledge_file


class ObsidianStorage:
    """Obsidian 知识存储器"""

    # 通用子目录列表（不限项目）
    SUBDIRS = ["python", "stock", "data", "bug", "pattern", "tool", "uncategorized"]

    # 项目内子目录列表
    PROJECT_SUBDIRS = ["数据获取", "问题记录", "架构设计", "回测策略", "实时数据", "其他"]

    def __init__(self, vault_path: Optional[str] = None):
        """
        初始化存储器

        Args:
            vault_path: Obsidian vault 路径，默认从配置读取
        """
        self._vault_path = vault_path
        self._config = None

    @property
    def vault_path(self) -> Path:
        """获取 vault 路径"""
        if self._vault_path:
            return Path(self._vault_path)

        # 从配置读取
        if self._config is None:
            try:
                if __name__ == "__main__" and __package__ is None:
                    from src.utils.config import get_config
                else:
                    from ..utils.config import get_config
                self._config = get_config()
            except Exception:
                # 默认路径
                return Path("D:/7mydatabase/knowledge/codeing")

        vault_path = self._config.get("knowledge.vault_path")
        if not vault_path:
            raise ValueError("配置缺失: knowledge.vault_path")

        return Path(vault_path)

    def _ensure_dirs(self, project: str = "") -> None:
        """确保目录结构存在"""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        if project:
            # 项目级目录
            project_dir = self.vault_path / project
            project_dir.mkdir(parents=True, exist_ok=True)
            for subdir in self.PROJECT_SUBDIRS:
                (project_dir / subdir).mkdir(parents=True, exist_ok=True)
        else:
            for subdir in self.SUBDIRS:
                (self.vault_path / subdir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_filename(name: str, max_length: int = 100) -> str:
        """
        清理文件名，移除非法字符

        Args:
            name: 原始名称
            max_length: 最大长度

        Returns:
            安全的文件名
        """
        # Windows 文件名非法字符
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        result = name
        for char in illegal_chars:
            result = result.replace(char, "_")
        # 替换空格
        result = result.replace(" ", "_")
        # 移除连续下划线
        while "__" in result:
            result = result.replace("__", "_")
        # 截断长度
        if len(result) > max_length:
            result = result[:max_length]
        return result.strip("_")

    def save_knowledge(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        category: str = "",
        project: str = "",
        source: str = "My_Stocks",
        status: str = "active",
        filename: Optional[str] = None
    ) -> Path:
        """
        保存知识到 Obsidian

        Args:
            title: 知识标题
            content: 知识内容（Markdown 格式）
            tags: 标签列表
            category: 分类（python/stock/data/bug/pattern/tool 或项目子分类）
            project: 项目名称（如 my_stocks），为空时使用通用分类
            source: 来源
            status: 状态
            filename: 自定义文件名（不含扩展名）

        Returns:
            保存的文件路径
        """
        self._ensure_dirs(project=project)

        # 生成文件名
        if not filename:
            date_str = datetime.now().strftime("%Y%m%d")
            safe_title = self._sanitize_filename(title)
            filename = f"{date_str}_{safe_title}"

        # 确定子目录
        if project:
            subdir = category if category in self.PROJECT_SUBDIRS else "其他"
            file_path = self.vault_path / project / subdir / f"{filename}.md"
        else:
            subdir = category if category in self.SUBDIRS else "uncategorized"
            file_path = self.vault_path / subdir / f"{filename}.md"

        # 如果没有提供标签，使用分类默认标签
        if tags is None:
            tags = KnowledgeTemplates.get_tags_for_category(category, project)

        # 生成完整内容
        full_content = create_knowledge_file(
            title=title,
            content=content,
            tags=tags,
            category=category,
            project=project,
            source=source,
            status=status
        )

        # 写入文件
        file_path.write_text(full_content, encoding="utf-8")
        return file_path

    def save_bug_fix(
        self,
        title: str,
        bug_desc: str,
        root_cause: str,
        solution: str,
        code_snippets: Optional[List[str]] = None,
        related_knowledge: Optional[List[str]] = None
    ) -> Path:
        """
        保存 Bug 修复知识

        Args:
            title: 知识标题
            bug_desc: Bug 描述
            root_cause: 根本原因
            solution: 解决方案
            code_snippets: 代码片段
            related_knowledge: 相关知识

        Returns:
            保存的文件路径
        """
        content = KnowledgeTemplates.bug_fix_template(
            bug_desc=bug_desc,
            root_cause=root_cause,
            solution=solution,
            code_snippets=code_snippets,
            related_knowledge=related_knowledge
        )

        return self.save_knowledge(
            title=title,
            content=content,
            category="bug"
        )

    def save_pattern(
        self,
        name: str,
        description: str,
        code: str,
        scenarios: Optional[List[str]] = None,
        pros: Optional[List[str]] = None,
        cons: Optional[List[str]] = None,
        related_patterns: Optional[List[str]] = None
    ) -> Path:
        """
        保存设计模式知识

        Args:
            name: 模式名称
            description: 模式描述
            code: 代码示例
            scenarios: 应用场景
            pros: 优点
            cons: 缺点
            related_patterns: 相关模式

        Returns:
            保存的文件路径
        """
        content = KnowledgeTemplates.pattern_template(
            name=name,
            description=description,
            code=code,
            scenarios=scenarios,
            pros=pros,
            cons=cons,
            related_patterns=related_patterns
        )

        return self.save_knowledge(
            title=name,
            content=content,
            category="pattern"
        )

    def save_daily_summary(
        self,
        date: Optional[str] = None,
        items: Optional[List[str]] = None,
        problems: Optional[List[str]] = None,
        todo: Optional[List[str]] = None
    ) -> Path:
        """
        保存每日总结

        Args:
            date: 日期，默认今天
            items: 今日收获
            problems: 问题与解决
            todo: 待深入学习

        Returns:
            保存的文件路径
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        content = KnowledgeTemplates.daily_summary_template(
            date=date,
            items=items,
            problems=problems,
            todo=todo
        )

        return self.save_knowledge(
            title=f"每日知识总结 - {date}",
            content=content,
            category="tool",
            filename=f"每日总结_{date.replace('-', '')}"
        )

    def save_stock_decision(
        self,
        symbol: str,
        name: str,
        decision_type: str,
        reason: str,
        result: Optional[str] = None,
        lessons: Optional[List[str]] = None
    ) -> Path:
        """
        保存股票决策知识

        Args:
            symbol: 股票代码
            name: 股票名称
            decision_type: 决策类型
            reason: 决策原因
            result: 结果分析
            lessons: 经验教训

        Returns:
            保存的文件路径
        """
        content = KnowledgeTemplates.stock_decision_template(
            symbol=symbol,
            name=name,
            decision_type=decision_type,
            reason=reason,
            result=result,
            lessons=lessons
        )

        date_str = datetime.now().strftime("%Y%m%d")
        return self.save_knowledge(
            title=f"{symbol} {name} - {decision_type}决策",
            content=content,
            category="stock",
            filename=f"{symbol}_{decision_type}_{date_str}"
        )

    def list_knowledge(
        self,
        tag: Optional[str] = None,
        category: Optional[str] = None,
        project: Optional[str] = None,
        limit: int = 20
    ) -> List[Path]:
        """
        列出知识文件

        Args:
            tag: 按标签过滤
            category: 按分类过滤
            project: 按项目过滤
            limit: 返回数量限制

        Returns:
            文件路径列表
        """
        files = []

        # 确定搜索目录
        if project:
            project_dir = self.vault_path / project
            if category and category in self.PROJECT_SUBDIRS:
                search_dirs = [project_dir / category]
            else:
                search_dirs = [project_dir / s for s in self.PROJECT_SUBDIRS]
        elif category and category in self.SUBDIRS:
            search_dirs = [self.vault_path / category]
        else:
            # 搜索所有目录（通用 + 所有项目）
            search_dirs = [self.vault_path / s for s in self.SUBDIRS]
            # 也搜索项目目录
            for d in self.vault_path.iterdir():
                if d.is_dir() and d.name not in self.SUBDIRS:
                    for ps in self.PROJECT_SUBDIRS:
                        sub = d / ps
                        if sub.exists():
                            search_dirs.append(sub)

        # 搜索文件
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for md_file in search_dir.glob("*.md"):
                if tag:
                    # 检查文件是否包含标签
                    content = md_file.read_text(encoding="utf-8")
                    if tag in content:
                        files.append(md_file)
                else:
                    files.append(md_file)

        # 按修改时间排序
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        return files[:limit]

    def read_knowledge(self, file_path: Path) -> Dict[str, Any]:
        """
        读取知识文件

        Args:
            file_path: 文件路径

        Returns:
            包含 frontmatter 和 content 的字典
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        # 解析 frontmatter
        result = {
            "path": str(file_path),
            "frontmatter": {},
            "content": content
        }

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                import yaml
                try:
                    result["frontmatter"] = yaml.safe_load(parts[1]) or {}
                    result["content"] = parts[2].strip()
                except yaml.YAMLError:
                    pass

        return result

    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索知识

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            匹配的知识列表
        """
        results = []
        query_lower = query.lower()

        for file_path in self.list_knowledge(limit=100):
            try:
                content = file_path.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    results.append({
                        "path": str(file_path),
                        "name": file_path.stem,
                        "preview": content[:200] + "..." if len(content) > 200 else content
                    })
            except Exception:
                continue

            if len(results) >= limit:
                break

        return results

    def delete_knowledge(self, file_path: Path) -> bool:
        """
        删除知识文件

        Args:
            file_path: 文件路径

        Returns:
            是否删除成功
        """
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False


def get_storage(vault_path: Optional[str] = None) -> ObsidianStorage:
    """
    获取存储器实例

    Args:
        vault_path: vault 路径

    Returns:
        ObsidianStorage 实例
    """
    return ObsidianStorage(vault_path)


if __name__ == "__main__":
    print("=" * 50)
    print("Obsidian 存储模块测试")
    print("=" * 50)

    try:
        storage = ObsidianStorage()
        print(f"[OK] Vault 路径: {storage.vault_path}")

        # 测试保存知识
        test_path = storage.save_knowledge(
            title="测试知识",
            content="# 测试知识\n\n这是一个测试知识文件。",
            category="python"
        )
        print(f"[OK] 保存测试知识: {test_path}")

        # 测试列出知识
        files = storage.list_knowledge(limit=5)
        print(f"[OK] 列出知识: {len(files)} 个文件")

        # 测试搜索知识
        results = storage.search_knowledge("测试", limit=5)
        print(f"[OK] 搜索知识: {len(results)} 个结果")

        # 清理测试文件
        if test_path.exists():
            test_path.unlink()
            print("[OK] 清理测试文件")

        print("\n" + "=" * 50)
        print("所有测试通过")
        print("=" * 50)

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        raise