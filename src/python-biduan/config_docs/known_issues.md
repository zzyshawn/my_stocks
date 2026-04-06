# 已知问题记录

## 1. 生成的 HTML 图表无法显示

**问题描述：**
- 使用 pyecharts 生成的 HTML 图表文件打开后显示空白页面
- 文件大小正常（约1.2MB），HTML 结构完整
- 网络连接正常，CDN 资源应该可以加载

**可能原因：**
1. pyecharts 版本兼容性问题（当前版本 2.1.0）
2. 本地文件打开时的浏览器安全限制
3. JS 资源加载时机问题

**影响文件：**
- `chanlun/visualization/pyecharts_plotter.py`

**待调查：**
- 检查浏览器控制台是否有 JS 错误
- 尝试使用 HTTP 服务器打开文件
- 检查 pyecharts 是否需要配置本地 JS 资源
- 对比 demo 项目的 HTML 输出格式

**记录时间：** 2026-03-22
