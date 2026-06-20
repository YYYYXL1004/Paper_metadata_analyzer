# 学术论文元数据分析工具

## 一、项目介绍

本项目是 Python 课程大作业“学术论文元数据分析工具”。系统可以通过 OpenAlex、CrossRef 和 arXiv 学术 API 获取真实论文元数据，完成论文检索、二次筛选、SQLite 存储、统计分析、可视化展示、CSV 导出和相关论文推荐。

项目重点覆盖网络请求、JSON/XML 解析、正则表达式、函数模块化、SQLite 数据库、文件导出、matplotlib 可视化、NumPy 合作网络分析和 Flask Web 页面等课程要求。

## 二、主要功能

- 论文检索：输入关键词、DOI 或研究主题，实时调用 OpenAlex/CrossRef/arXiv API 获取论文元数据，单次最多可拉取 5000 条（OpenAlex 通过 cursor 自动分页，每页 200 条）。
- 元数据解析：提取标题、作者、年份、DOI、期刊、引用次数、摘要、URL 等字段。
- 正则提取：使用正则表达式提取 DOI、年份和关键词。
- 数据库存储：使用 SQLite 保存论文、作者、关键词及关联关系，包含性能优化索引。
- 搜索历史：首页显示最近 5 次搜索记录，点击即可快速复用缓存数据。
- 搜索后实时筛选：在结果页用客户端 JS 即时按排序方式（相关度/引用/年份/标题）、最低引用、年份范围、数据源和关键词进行二次过滤与重排，无需重新请求 API。
- 数据分析：围绕本次关键词检索返回的论文集合，统计年度趋势、关键词频率、引用分布、期刊排行、作者排行和数据源占比。
- 专业指标：计算相关性分数、综合排序分、平均引用、中位引用、引用标准差、DOI 覆盖率、近五年论文数和高被引论文排行。
- 合作网络：使用 NumPy 构建作者合作邻接矩阵，分析合作边数、网络密度和作者中心度，并生成网络可视化图（节点大小表示合作次数）。
- 单篇论文详情与分析：进入论文详情页可看到完整摘要、关键词、本次检索集合中的引用排位、引用对比图（与同年论文平均/最高/最低对比），以及基于关键词相似度+引用得分+年份新鲜度的相关推荐。
- 文件导出：将本次检索结果导出为 CSV 或 BibTeX 格式（学术引用标准格式）。
- Web 展示：使用 Flask 提供论文检索、结果展示、单篇分析、整体仪表盘和推荐页面。

## 三、安装与运行方式

### 1. 进入项目目录

```powershell
cd Paper_metadata_analyzer
```

### 2. 安装依赖

```powershell
pip install -r requirements.txt
```

### 3. 启动项目

```powershell
python app.py
```

### 4. 打开浏览器访问

```text
http://127.0.0.1:5000
```

如果 5000 端口被占用，可以在 PowerShell 中指定其他端口：

```powershell
$env:PORT=5004
python app.py
```

论文检索默认实时调用远程学术 API。OpenAlex 引用数据最全，CrossRef 会补充高引用候选，arXiv 仅覆盖 STEM 预印本且通常不提供引用次数（引用数可能为 0）。OpenAlex 通过 cursor 翻页累计抓取，因此可一次性拉到上千条候选；ranker 不会再把低相关性论文硬性剔除，而是降权排序，避免漏掉 OpenAlex 宽匹配返回的扩展结果。

若 OpenAlex 或 arXiv 网络超时，系统会自动回退到 CrossRef；若远程 API 全部不可用，则使用本地真实 API 缓存，不会把演示数据伪装成检索结果。

> 注：首次运行会自动创建 `data/papers.db` 与 `exports/` 目录用于本地缓存与 CSV 导出，这两个目录已加入 `.gitignore`，不会被纳入版本控制。

## 四、功能截图

### 1. 论文检索首页

![论文检索首页](docs/screenshots/home.png)

### 2. 真实 API 检索结果

![真实 API 检索结果](docs/screenshots/search_results.png)

### 3. 数据分析仪表盘

![数据分析仪表盘](docs/screenshots/analysis_dashboard.png)

## 五、项目结构

```text
Paper_metadata_analyzer/
├─ app.py                  # Flask 主程序与路由
├─ config.py               # 路径、API 地址、上限和默认参数配置
├─ requirements.txt        # 第三方依赖
├─ README.md               # 项目说明文档
├─ data/                   # SQLite 数据库目录（运行时自动生成，已被 .gitignore 忽略）
│  └─ papers.db            # 检索结果本地缓存
├─ exports/                # CSV 导出目录（运行时自动生成）
│  └─ papers.csv           # 单次检索结果的 CSV 导出
├─ docs/
│  └─ screenshots/         # README 功能截图
├─ static/
│  ├─ css/style.css        # 页面样式
│  └─ charts/              # matplotlib 生成的图表
├─ templates/
│  ├─ base.html            # 公共布局
│  ├─ index.html           # 首页 / 检索表单
│  ├─ results.html         # 结果列表 + 客户端筛选面板
│  ├─ paper_detail.html    # 单篇论文详情与分析
│  ├─ analysis.html        # 整体分析仪表盘
│  └─ recommend.html       # 旧推荐页（保留兼容）
└─ src/
   ├─ api_client.py        # OpenAlex/CrossRef/arXiv API 请求与 cursor 分页
   ├─ parser.py            # JSON/XML 响应解析
   ├─ extractor.py         # 正则提取与关键词处理
   ├─ database.py          # SQLite 数据库操作
   ├─ ranker.py            # 相关性评分 + 综合排序（低相关性降权而非剔除）
   ├─ analyzer.py          # 统计分析与自动洞察
   ├─ network.py           # NumPy 作者合作网络
   ├─ recommender.py       # 相关论文推荐
   ├─ visualizer.py        # matplotlib 可视化
   └─ exporter.py          # CSV 导出
```

## 六、评分点对应

| 评分要求 | 项目实现 |
|---|---|
| 网络编程：调用学术 API 获取论文数据 | `src/api_client.py` 调用 OpenAlex/CrossRef/arXiv，含 cursor 翻页 |
| 字典/列表解析嵌套 JSON 响应 | `src/parser.py` 解析三家 API 返回的 JSON/XML |
| 正则表达式提取 DOI、年份、关键词 | `src/extractor.py` 使用正则表达式处理文本 |
| 函数模块化设计数据获取和分析流程 | `src/` 下按功能拆分多个模块 |
| SQLite 存储论文元数据 | `src/database.py` 创建论文、作者、关键词及关系表 |
| 文件操作：导出分析结果为 CSV | `src/exporter.py` 导出 `exports/papers.csv` |
| matplotlib 可视化发表趋势、关键词云 | `src/visualizer.py` 生成趋势图、关键词图、词云等 |
| NumPy 统计分析引用网络、合著关系 | `src/network.py` 构建作者合作邻接矩阵 |
| 基于关键词重合度的相关论文推荐 | `src/recommender.py` 计算综合推荐分数 |
| Flask 构建论文搜索与可视化 Web 页面 | `app.py` 和 `templates/` 提供 Web 界面，含 `/paper/<id>` 单篇分析路由 |

## 七、代码风格与注释说明

- 代码按功能拆分为独立模块，避免所有逻辑堆在一个文件中。
- 函数命名使用清晰的英文动词短语，例如 `fetch_openalex_paged`、`parse_crossref_response`、`compute_cohort_position`。
- 数据库、API、解析、排序、分析、推荐、可视化和导出逻辑分别放在不同文件中，便于阅读和维护。
- 对复杂逻辑保留了必要注释或清晰函数名，例如 API 重试、cursor 分页、SQLite 建表、作者合作矩阵、推荐评分等。
- 页面模板和样式文件分离，HTML 模板只负责结构，CSS 负责视觉表现；结果页二次筛选由内嵌 vanilla JS 实现，无需额外依赖。

## 八、推荐演示流程

1. 启动应用并访问首页，注意首页显示的”最近搜索”历史记录（如果有）。
2. 输入关键词，例如 `deep learning`，选择数据源 OpenAlex，数量上限填 200。
3. 点击”调用 API 检索论文”，等待 OpenAlex 通过 cursor 分页拉取结果。
4. 在结果页顶部使用紧凑筛选条：调整排序（引用高→低、年份新→旧）、设置最低引用次数、年份范围、来源或输入关键词二次过滤，实时观察列表变化。
5. 点击任一论文卡片下方”查看详情与分析”，进入 `/paper/<id>` 单篇详情页，查看：
   - 完整摘要和关键词
   - 本次检索集合中的引用排位
   - **引用对比图**（与同年论文的平均/最高/最低引用对比）
   - 基于关键词相似度的相关推荐论文
6. 返回结果页，点击底部”查看整体分析”，进入 `/analysis` 仪表盘查看 **9 张专业图表**：
   - 年度发文趋势
   - 高频关键词柱状图
   - 引用次数分布
   - 关键词词云
   - 期刊/来源排行
   - 高产作者排行
   - 数据源占比饼图
   - 年度平均引用趋势
   - **作者合作网络可视化**（新增，节点大小表示合作次数）
7. 点击”导出 CSV”或”导出 BibTeX”，下载当前检索结果（BibTeX 格式可直接导入文献管理工具）。
8. 返回首页，点击”最近搜索”中的历史关键词，体验秒级加载（从本地缓存）。
