# 学术论文元数据分析工具

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

一个功能完善的学术论文检索与可视化分析系统

[功能特性](#功能特性) • [快速开始](#快速开始) • [功能演示](#功能演示) • [项目结构](#项目结构)

</div>

---

## 项目介绍

本项目是一个基于 Python + Flask 的学术论文元数据分析工具，支持通过 **OpenAlex**、**CrossRef** 和 **arXiv** 三大学术 API 获取真实论文数据，提供论文检索、数据分析、可视化展示、文献导出等完整功能。

### 核心技术栈

- **后端框架**：Flask 3.0+
- **数据存储**：SQLite（含索引优化）
- **数据分析**：NumPy、pandas
- **可视化**：matplotlib、wordcloud
- **网络请求**：requests（含自动重试与降级）

### 设计亮点

- 🔍 **智能检索**：支持 cursor 分页，单次可拉取 5000+ 条论文记录
- 📊 **专业分析**：9 张可视化图表 + 作者合作网络 + 引用对比
- ⚡ **实时筛选**：客户端 JavaScript 二次过滤，无需重新请求 API
- 💾 **本地缓存**：搜索历史自动保存，秒级加载
- 📥 **标准导出**：支持 CSV 和 BibTeX 格式（可直接导入文献管理工具）
- 🔄 **自动降级**：API 超时时自动切换备用数据源

---

## 功能特性

### 1. 论文检索与管理

- **多源检索**：整合 OpenAlex、CrossRef、arXiv 三大学术 API
- **智能分页**：OpenAlex 通过 cursor 自动翻页，每页 200 条
- **元数据解析**：提取标题、作者、年份、DOI、期刊、引用次数、摘要等字段
- **正则处理**：使用正则表达式提取 DOI、年份和关键词
- **搜索历史**：首页展示最近 5 次搜索，点击即可快速复用

### 2. 数据分析与可视化

#### 整体分析仪表盘（9 张图表）

1. **年度发文趋势**：时间序列展示论文产出变化
2. **高频关键词柱状图**：提取研究热点
3. **引用次数分布**：直方图展示引用模式
4. **关键词词云**：可视化研究主题
5. **期刊/来源排行**：识别顶级发表渠道
6. **高产作者排行**：发现领域核心学者
7. **数据源占比饼图**：对比三大 API 覆盖率
8. **年度平均引用趋势**：分析学术影响力变化
9. **作者合作网络**：NumPy 构建邻接矩阵，节点大小表示合作强度

#### 单篇论文深度分析

- **引用排位**：当前检索集合中的引用排名
- **引用对比图**：与同年论文的平均/最高/最低引用对比
- **相关推荐**：基于关键词相似度 + 引用得分 + 年份新鲜度

### 3. 高级功能

- **实时二次筛选**：客户端 JavaScript 按排序方式、引用次数、年份范围、数据源、关键词即时过滤
- **专业指标计算**：相关性分数、综合排序分、平均/中位/标准差引用、DOI 覆盖率、高被引论文排行
- **合作网络分析**：合作边数、网络密度、作者中心度
- **文件导出**：CSV（数据分析）和 BibTeX（学术引用）双格式

---

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/Paper_metadata_analyzer.git
cd Paper_metadata_analyzer

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
python app.py

# 4. 打开浏览器访问
# http://127.0.0.1:5000
```

### 自定义端口

如果 5000 端口被占用：

**Windows (PowerShell)**
```powershell
$env:PORT=5004
python app.py
```

**Linux/macOS**
```bash
PORT=5004 python app.py
```

### 首次运行说明

- 应用会自动创建 `data/papers.db`（SQLite 数据库）和 `exports/`（导出目录）
- 这两个目录已加入 `.gitignore`，不会被版本控制
- 首次检索会调用远程 API，后续可从缓存快速加载

---

## 功能演示

### 1. 论文检索首页

支持关键词搜索、数据源选择、数量限制，展示最近搜索历史。

![论文检索首页](docs/screenshots/home.png)

### 2. 真实 API 检索结果

展示论文列表，支持实时排序、筛选、二次过滤，无需重新请求 API。

![真实 API 检索结果](docs/screenshots/search_results.png)

### 3. 数据分析仪表盘

9 张专业图表，包括年度趋势、关键词分析、引用分布、作者合作网络等。

![数据分析仪表盘](docs/screenshots/analysis_dashboard.png)

---

## 推荐演示流程

1. **首页检索**
   - 访问首页，查看"最近搜索"历史记录
   - 输入关键词（如 `deep learning`），选择数据源 OpenAlex，设置数量上限 200

2. **结果浏览与筛选**
   - 等待 API 返回结果（OpenAlex 会自动翻页）
   - 使用顶部筛选条调整排序（引用/年份）、设置最低引用、年份范围、来源过滤
   - 实时观察列表变化（纯客户端筛选，秒级响应）

3. **单篇论文分析**
   - 点击任一论文卡片下方"查看详情与分析"
   - 查看完整摘要、关键词、引用排位、**引用对比图**、相关推荐

4. **整体分析仪表盘**
   - 点击"查看整体分析"进入 `/analysis` 路由
   - 浏览 9 张图表，包括新增的**作者合作网络可视化**

5. **数据导出**
   - 点击"导出 CSV"或"导出 BibTeX"
   - BibTeX 格式可直接导入 Zotero、Mendeley 等文献管理工具

6. **历史快速加载**
   - 返回首页，点击"最近搜索"中的历史关键词
   - 体验秒级加载（从本地 SQLite 缓存读取）

---

## 项目结构

```
Paper_metadata_analyzer/
├── app.py                  # Flask 主程序与路由
├── config.py               # 路径、API 地址、上限和默认参数配置
├── requirements.txt        # 第三方依赖
├── README.md               # 项目说明文档
├── data/                   # SQLite 数据库目录（自动生成，已忽略）
│   └── papers.db           # 检索结果本地缓存
├── exports/                # CSV/BibTeX 导出目录（自动生成）
│   ├── papers.csv
│   └── papers.bib
├── docs/
│   └── screenshots/        # README 功能截图
├── static/
│   ├── css/
│   │   └── style.css       # 页面样式
│   └── charts/             # matplotlib 生成的图表
├── templates/
│   ├── base.html           # 公共布局
│   ├── index.html          # 首页 / 检索表单
│   ├── results.html        # 结果列表 + 客户端筛选面板
│   ├── paper_detail.html   # 单篇论文详情与分析
│   ├── analysis.html       # 整体分析仪表盘
│   └── recommend.html      # 旧推荐页（兼容保留）
└── src/
    ├── api_client.py       # OpenAlex/CrossRef/arXiv API 请求与 cursor 分页
    ├── parser.py           # JSON/XML 响应解析
    ├── extractor.py        # 正则提取与关键词处理
    ├── database.py         # SQLite 数据库操作
    ├── ranker.py           # 相关性评分 + 综合排序（降权策略）
    ├── analyzer.py         # 统计分析与自动洞察
    ├── network.py          # NumPy 作者合作网络
    ├── recommender.py      # 相关论文推荐
    ├── visualizer.py       # matplotlib 可视化
    └── exporter.py         # CSV/BibTeX 导出
```

---

## 技术实现亮点

### 1. 网络请求与 API 集成

- **多源 API**：`src/api_client.py` 调用 OpenAlex/CrossRef/arXiv
- **自动分页**：OpenAlex 使用 cursor 翻页，单次可拉取 5000+ 条
- **重试机制**：网络超时自动重试，失败后降级到备用数据源
- **缓存优化**：本地 SQLite 缓存历史检索，避免重复请求

### 2. 数据解析与处理

- **多格式解析**：`src/parser.py` 处理 JSON/XML 响应
- **正则提取**：`src/extractor.py` 提取 DOI、年份、关键词
- **模块化设计**：按功能拆分 10 个独立模块，便于维护

### 3. 数据库与存储

- **SQLite**：`src/database.py` 创建论文、作者、关键词及关联表
- **性能优化**：为高频查询字段添加索引
- **关系建模**：多对多关系表实现作者-论文、论文-关键词关联

### 4. 统计分析与可视化

- **NumPy**：`src/network.py` 构建作者合作邻接矩阵
- **matplotlib**：`src/visualizer.py` 生成 9 张专业图表
- **wordcloud**：生成关键词词云
- **专业指标**：相关性分数、引用统计、DOI 覆盖率等

### 5. 推荐算法

- **综合评分**：关键词相似度（余弦相似度）+ 引用归一化得分 + 年份新鲜度
- **动态权重**：`src/recommender.py` 实现可配置的多维度推荐

### 6. Web 界面

- **Flask 路由**：`app.py` 提供检索、结果、详情、分析、推荐等路由
- **客户端筛选**：vanilla JavaScript 实现实时过滤，无需后端交互
- **响应式设计**：CSS 适配不同屏幕尺寸

---

## 课程要求覆盖

| 评分要求 | 项目实现 |
|---------|---------|
| 网络编程：调用学术 API 获取论文数据 | `src/api_client.py` 调用 OpenAlex/CrossRef/arXiv，含 cursor 翻页 |
| 字典/列表解析嵌套 JSON 响应 | `src/parser.py` 解析三家 API 返回的 JSON/XML |
| 正则表达式提取 DOI、年份、关键词 | `src/extractor.py` 使用正则表达式处理文本 |
| 函数模块化设计数据获取和分析流程 | `src/` 下按功能拆分 10 个模块 |
| SQLite 存储论文元数据 | `src/database.py` 创建论文、作者、关键词及关系表 |
| 文件操作：导出分析结果为 CSV | `src/exporter.py` 导出 CSV 和 BibTeX |
| matplotlib 可视化发表趋势、关键词云 | `src/visualizer.py` 生成 9 张图表 + 词云 |
| NumPy 统计分析引用网络、合著关系 | `src/network.py` 构建作者合作邻接矩阵 |
| 基于关键词重合度的相关论文推荐 | `src/recommender.py` 计算综合推荐分数 |
| Flask 构建论文搜索与可视化 Web 页面 | `app.py` 和 `templates/` 提供完整 Web 界面 |

---

## 代码风格

- ✅ 按功能拆分为独立模块，避免逻辑耦合
- ✅ 函数命名使用清晰的英文动词短语（如 `fetch_openalex_paged`、`compute_cohort_position`）
- ✅ 数据库、API、解析、排序、分析、推荐、可视化和导出逻辑分别独立
- ✅ 对复杂逻辑保留必要注释（API 重试、cursor 分页、作者合作矩阵等）
- ✅ HTML 模板与 CSS 分离，vanilla JavaScript 实现客户端交互

---

## 常见问题

### Q1: API 请求超时怎么办？

A: 系统会自动重试 3 次，失败后降级到备用数据源（OpenAlex → CrossRef → 本地缓存）。

### Q2: 为什么 arXiv 的论文引用次数为 0？

A: arXiv 是预印本平台，通常不提供引用次数统计。建议优先使用 OpenAlex 或 CrossRef。

### Q3: 如何清空搜索历史？

A: 删除 `data/papers.db` 文件，重启应用即可。

### Q4: 导出的 BibTeX 格式不正确？

A: 请确保论文有 DOI 或完整的作者/年份信息，系统会自动生成符合标准的 BibTeX 条目。

---

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

## 致谢

- [OpenAlex](https://openalex.org/) - 开放学术图谱 API
- [CrossRef](https://www.crossref.org/) - DOI 注册机构 API
- [arXiv](https://arxiv.org/) - 预印本论文平台

---

<div align="center">

**如果觉得项目有帮助，欢迎 ⭐ Star！**

</div>
