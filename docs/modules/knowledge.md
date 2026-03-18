# 知识总结模块需求

## 1. 功能描述

自动总结分析过程中的知识经验，形成可复用的知识库。支持 Obsidian 格式存储，使用 YAML frontmatter 和标签系统。

## 2. 实现状态

| 编号 | 需求项 | 优先级 | 状态 | 描述 |
|------|--------|--------|------|------|
| R8.1 | Obsidian 存储 | P0 | ✅ 已实现 | 知识保存到 Obsidian vault |
| R8.2 | 标签系统 | P0 | ✅ 已实现 | 支持 Obsidian 格式标签层次结构 |
| R8.3 | 知识分类 | P0 | ✅ 已实现 | python/stock/data/bug/pattern/tool 六大分类 |
| R8.4 | YAML Frontmatter | P0 | ✅ 已实现 | 自动生成 YAML 元数据 |
| R8.5 | Bug 修复经验 | P1 | ✅ 已实现 | Bug 描述、原因、解决方案模板 |
| R8.6 | 设计模式记录 | P2 | ✅ 已实现 | 模式描述、代码示例、应用场景 |
| R8.7 | 每日总结生成 | P1 | ✅ 已实现 | 自动生成每日开发知识总结 |
| R8.8 | 知识检索 | P1 | ✅ 已实现 | 按标签、分类、日期检索知识 |
| R8.9 | 决策总结 | P1 | 📋 计划中 | 股票决策成功/失败案例记录 |
| R8.10 | AI 辅助分析 | P2 | 📋 计划中 | AI 辅助知识提炼和关联分析 |

## 3. 模块结构

```
src/knowledge/
├── __init__.py          # 模块入口，导出主要类和函数
├── storage.py           # Obsidian 存储集成
├── summary.py           # 知识总结核心逻辑
└── templates.py         # 知识模板生成器
```

## 4. 核心类设计

### 4.1 ObsidianStorage (storage.py)

知识文件存储、YAML frontmatter 生成、目录管理。

```python
class ObsidianStorage:
    def __init__(self, vault_path: str = None)
    def save_knowledge(self, title, content, tags, category, ...) -> Path
    def save_bug_fix(self, title, bug_desc, root_cause, solution, ...) -> Path
    def save_pattern(self, name, description, code, ...) -> Path
    def save_daily_summary(self, date, items, problems, todo) -> Path
    def list_knowledge(self, tag, category, limit) -> List[Path]
    def search_knowledge(self, query, limit) -> List[Dict]
    def read_knowledge(self, file_path) -> Dict
    def delete_knowledge(self, file_path) -> bool
```

### 4.2 KnowledgeSummarizer (summary.py)

知识总结、分类、检索。

```python
class KnowledgeSummarizer:
    def __init__(self, vault_path: str = None)
    def summarize_bug_fix(self, bug_description, root_cause, solution, ...) -> str
    def summarize_pattern(self, pattern_name, description, code_example, ...) -> str
    def summarize_coding(self, title, background, core_content, ...) -> str
    def summarize_stock_decision(self, symbol, name, decision_type, ...) -> str
    def generate_daily_summary(self, date, items, problems, todo) -> str
    def search_knowledge(self, query, limit) -> List[Dict]
    def list_recent_knowledge(self, limit) -> List[Dict]
    def get_knowledge_by_tag(self, tag, limit) -> List[Dict]
```

### 4.3 KnowledgeTemplates (templates.py)

知识模板生成器，支持多种模板类型。

```python
class KnowledgeTemplates:
    @staticmethod
    def generate_frontmatter(title, tags, source, status, date) -> str

    @staticmethod
    def bug_fix_template(bug_desc, root_cause, solution, code_snippets, ...) -> str

    @staticmethod
    def pattern_template(name, description, code, scenarios, pros, cons, ...) -> str

    @staticmethod
    def daily_summary_template(date, items, problems, todo) -> str

    @staticmethod
    def stock_decision_template(symbol, name, decision_type, reason, ...) -> str

    @staticmethod
    def coding_knowledge_template(title, background, core_content, ...) -> str
```

## 5. 标签系统

### 标签层次结构

```
#coding                    # 编程总标签
  #coding/python           # Python 相关
  #coding/stock            # 股票分析相关
  #coding/data             # 数据处理相关
  #coding/bug              # Bug 修复经验
  #coding/pattern          # 设计模式
  #coding/tool             # 工具使用
```

### 标签使用规范

| 标签 | 用途 | 示例知识点 |
|------|------|-----------|
| `#coding/python` | Python 编程知识 | 类型提示、装饰器、异步编程 |
| `#coding/stock` | 股票分析知识 | 技术指标、策略、回测 |
| `#coding/data` | 数据处理知识 | pandas、数据清洗、格式转换 |
| `#coding/bug` | Bug 修复经验 | 错误原因、解决方案 |
| `#coding/pattern` | 设计模式 | 单例、工厂、观察者 |
| `#coding/tool` | 工具使用 | Obsidian、CLI、Git |

## 6. 配置参数

```yaml
# config/config.yaml
knowledge:
  enabled: true
  vault_path: "D:/7mydatabase/knowledge/codeing"
  auto_save: true
  tags:
    default: ["#coding"]
    categories:
      python: ["#coding", "#coding/python"]
      stock: ["#coding", "#coding/stock"]
      data: ["#coding", "#coding/data"]
      bug: ["#coding", "#coding/bug"]
      pattern: ["#coding", "#coding/pattern"]
      tool: ["#coding", "#coding/tool"]
```

## 7. 使用示例

```python
from src.knowledge import KnowledgeSummarizer, ObsidianStorage

# 创建总结器
summarizer = KnowledgeSummarizer()

# 总结 Bug 修复
summarizer.summarize_bug_fix(
    bug_description="模块导入错误",
    root_cause="相对导入和绝对导入混用",
    solution="使用 try/except ImportError 处理",
    code_changes=["try: from .module import func\nexcept ImportError: from module import func"]
)

# 生成每日总结
summarizer.generate_daily_summary(
    items=["实现了知识模块", "修复了导入问题"],
    problems=["模块导入问题已解决"],
    todo=["深入学习 Obsidian 插件"]
)

# 搜索知识
results = summarizer.search_knowledge("导入", limit=10)

# 按标签获取知识
python_knowledge = summarizer.get_knowledge_by_tag("#coding/python")
```

## 8. 知识文件格式

```markdown
---
title: 知识标题
date: 2026-03-18
tags: [#coding, #coding/python, #coding/stock]
source: My_Stocks
status: active
---

# 知识标题

## 背景
知识的背景和上下文...

## 核心内容
具体知识点...

## 示例
代码示例...

## 相关知识
- [[其他相关知识点]]

## 应用场景
在哪些场景下使用...
```

## 9. 目录结构

```
D:/7mydatabase/knowledge/codeing/
├── python/              # Python 编程知识
│   └── YYYYMMDD_标题.md
├── stock/               # 股票分析知识
│   └── YYYYMMDD_标题.md
├── data/                # 数据处理知识
│   └── YYYYMMDD_标题.md
├── bug/                 # Bug 修复经验
│   └── YYYYMMDD_标题.md
├── pattern/             # 设计模式
│   └── YYYYMMDD_标题.md
├── tool/                # 工具使用
│   └── YYYYMMDD_标题.md
└── uncategorized/       # 未分类知识
    └── YYYYMMDD_标题.md
```

---

*最后更新: 2026-03-18*