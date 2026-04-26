# 知乎 / 微信文章 / V2EX 发布稿

适合发知乎专栏、微信公众号、V2EX。一稿多投，长度可截。

标题候选（按"被点开率"从高到低）：

1. **「我做投资，每年要做 30 场 ref check。每次手改稿子要 45 分钟。所以我做了这个开源工具。」**
2. **「让 ASR 转录稿"记住你怎么改"——开源了一个本地优先的逐字稿整理工具」**
3. **「ChatGPT 整理逐字稿每次都从零开始，太蠢。我做了个会复利的本地版本。」**

---

## 正文

我做投资，每年大约做 30 场 reference call。每场 60-90 分钟，录音转出来都是个 ASR 稿子——飞书妙记 / 通义听悟 / Whisper / PLAUD 都用过。

这些工具都很好，**给我 95% 对的稿子**。

剩下 5% 是地狱。

每一份稿子，我都要花 45 分钟改同样的几类错：

- Speaker 2 / Speaker 3 没人名
- 公司名 ASR 听错——"Dify" 听成 "DeFi"，"PingCAP" 听成 "PinkCup"，"Manus" 听成 "Minus"
- 测麦客套话还在里面（"听得见吗？"、"咱们开始？"）
- AI 工具自己拼的"本次访谈总结"模块要手删
- 行话术语前后不一致——"skip level" / "scalable" 乱混

最让人疯的是：**我每次改完，下一份新稿子又来一遍。** 我已经手改过 200 次的"Eileen 不是 Speaker 2"，模型不知道。我手改过 50 次的"Dify 不是 DeFi"，模型不记得。

我手改的每一刀，都没有沉淀成任何东西。

---

## 所以我做了 clearscript

→ Repo: https://github.com/Chen17-sq/clearscript
→ 在线: https://chen17-sq.github.io/clearscript/

最早是个个人用的 Claude skill。跑了上百次 ref check / 创始人访谈 / 投决会录音 / 播客整理之后，我开源了。

三个核心信念，按重要性排：

### 1. 你的转录稿不是训练数据

我跟受访人说"这是私下交流"——这个承诺**架构上**就要兑现，不能只是 SaaS 网站底部的一句"我们 30 天后会删除"。

clearscript 跑在你本机。稿子存在你自己的 `~/Documents/clearscript/projects/`。术语库是你自己的 SQLite 文件 `~/.local/share/clearscript/library/library.db`。**唯一的网络调用就是你授权的那次 LLM 请求**——你选 Claude 就只发 Anthropic，你选 Ollama 就完全不出本机。

没有账号、没有 telemetry、没有"匿名使用数据帮助我们改进"。删了就是删了，备份就用 `tar` 自己来，要 git 跟踪整个库自己 init。

### 2. ASR 是起点，不是交付物

整个行业都在卖你转录服务。但**没人解决"转完之后的脏活"**。

clearscript 不转录音频。它在 ASR 工具停下的地方接手——给 Speaker N 配上真名，把 Dify 听对，删掉 AI 摘要，统一标点，按说话人切段。

### 3. 记忆是护城河

LLM 每次都从零开始。这是它的根本短板。

clearscript 帮你**沉淀记忆**：

- 每个修过的说话人 → 进 speakers 表
- 每个修过的术语 → 进 terms 表（带 alias）
- 每个 "这种地方别动" 的偏好 → 进 negative_corrections
- 每次跑完，模型自己提议"建议你加入库的新词条"，一键 accept

跑到第 10 份稿子时，**clearscript 自己就能把 80% 的修正先做了**，你点 Run 之前。

---

## 用法（5 分钟跑通）

```bash
git clone https://github.com/Chen17-sq/clearscript.git
cd clearscript
uv sync
export DEEPSEEK_API_KEY=sk-你的key   # 或者 ANTHROPIC_API_KEY / GEMINI_API_KEY
uv run clearscript serve
```

浏览器自动打开 `http://127.0.0.1:7681`。Bauhaus 风格的本地单页：

1. 顶上选 provider（带"成本预览"，告诉你这次跑大概花多少钱）
2. 拖一份 .docx / .srt / .json / .txt 进 drop zone
3. 可选：briefing 里写 "Speaker 1 = 张三 (host); Speaker 2 = 李四 (Acme CEO); 涉及公司: Dify, Manus"
4. 点红色 Run 按钮
5. 右栏出来清理稿，可以**直接编辑**（自动存盘）
6. 切到 Diff 视图看哪些改了，每个改动有颜色标注（L1=蓝/L3=红/L3.5=橙）和 hover 原因
7. 跑完弹一个黄色面板"📚 本次为库带来 8 项更新"，勾选 Accept

成本：DeepSeek 大约 0.2 元跑一份 90 分钟稿子，Claude Opus 大约 1.5 美元，Ollama 免费。

---

## 不止是个 web app——也是个 Claude skill

有些朋友用 Claude Code 或者 Claude Agent SDK 做自己的 agent。

clearscript 同时打包成 `.skill` 文件，下载丢进 `~/.claude/skills/`，你的 agent 就有了同款的 7 层逐字稿整理能力。**两边共用同一份 prompt 源代码**——主项目改了 prompt，skill 自动跟着升级。

---

## 现在的状态 & 下一步

v0.0.7，本地能跑、能用、有界面。具体功能：

- 6 种输入格式（含飞书妙记 / 通义听悟 .docx）
- 5 个 provider adapter 覆盖 20+ 服务
- 长稿自动分块（90 分钟稿子能跑）
- inline 可编辑输出 + auto-save
- diff 高亮 + 跨改动 hover 解释
- 跑前成本预览
- 完整 project 历史（每次跑都存档）
- 库的 stats / 增删改 / 批量提议接受

下一个版本（v0.0.8）打算做：流式进度条、project re-run（换 model 重跑老稿）、跨 project 全文搜索。

---

## 这是个开源项目，我希望它有用

MIT 协议。代码在 https://github.com/Chen17-sq/clearscript

如果你也在做需要大量整理逐字稿的工作（VC、HR、记者、研究、播客、医疗访谈），欢迎试一试，给个 star，提 issue，或者直接 PR。

我会持续维护。每次自己用都还在改进。

---

## FAQ

**Q：跟 Otter / 通义 / 飞书妙记是什么关系？**

它们做转录，clearscript 做转录后的整理。你拿任何 ASR 工具的输出，喂给 clearscript。

**Q：为什么不直接用 ChatGPT？**

可以，但每次都从零开始。clearscript 的核心价值就是那个**会长大的本地术语库**——你的"institutional memory"，不会随浏览器关闭就消失。

**Q：90 分钟访谈跑得动吗？**

自动分块。一份 90 分钟稿子大概切成 8-12 块依次跑，结果拼回完整稿子。

**Q：我能用本地模型吗（隐私敏感）？**

能。配 Ollama 就完全离线。完全不需要联网，连 LLM 调用都不出本机。

**Q：Mac / Linux / Windows？**

都支持。CI 三个平台都过。v0.1 会出 PyInstaller 打包的桌面安装包（一键双击），现在还需要 Python + uv。
