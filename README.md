# collaborating-with-claude-code

中文 | [English](README_EN.md)

**Codex CLI** 的一个 skill ：通过一个 JSON bridge 脚本，把“代码审查 / 调试 / 方案对比”等任务委托给 **Anthropic Claude Code CLI**（默认模型：`claude-opus-4-6`），并以结构化 JSON 结果返回，便于在多模型协作中使用。

本仓库的核心入口是 `SKILL.md`（Codex skill 定义）以及 `scripts/claude_code_bridge.py`（桥接脚本）。

# 版本更新说明
### 修复了在claude cli@2.1.104中因参数不对
codex会降级直接使用claude cli命令使用的问题(非交互模式，执行完直接输出结果)；
关于脚本桥接和直接使用claude cli命令的差异如下：
✅ 结论：**如果不考虑兼容性和故障问题，作为我这种“总控调度 Claude 干活”的场景，桥接脚本通常效率更高。**

原因很直接：

- **桥接脚本更适合程序化调度**
  它会统一返回 JSON，像 `success / SESSION_ID / agent_messages` 这种结果我更容易自动接住、解析、复用。
- **多轮续跑更顺**
  桥接脚本天然带 `SESSION_ID`，后面继续追问、补充约束、让 Claude 接着干，会比我自己手动拼 `claude` 命令省事。
- **更适合做稳定工作流**
  比如“发任务 -> 收结果 -> 验收 -> 再追一轮”这种循环，桥接脚本更像一个接口层。

但如果换个角度：

- **原生 `claude` CLI 更直接**
  少一层封装，出问题更容易定位。
- **临时一次性任务**
  比如只跑一条实现命令、一次性让 Claude 干活，原生 CLI 往往更快上手。
- **可观察性更强**
  你能更清楚地看到 Claude CLI 本身的行为，而不是脚本包装后的行为。

所以可以这样理解：

- **长期协作 / 多轮调度 / 结构化集成**：桥接脚本效率更高
- **临时单次调用 / 排障 / 手工直控**：原生 `claude` CLI 更直接

一句话总结：

**桥接脚本更像“工程化接口”，原生 CLI 更像“手动直连终端”。**
对我这种要负责拆任务、派任务、验收结果的总控角色来说，正常情况下我会优先选桥接脚本。

哪种速度最快？
同一个任务下，**原生 `claude` CLI 直连通常会略快一点**，因为少了一层 Python 桥接包装。

但这个“更快”一般只是体感上的一点点差异，通常差在：
- 启动桥接脚本本身的开销
- 桥接脚本解析和包装 JSON 的开销
- 多一层进程转发

真正的大头其实还是：
- Claude 本身思考和执行任务的时间
- 读文件、改文件、跑命令的时间

所以实际可以这样理解：

- **单次、短任务**
  原生 `claude` CLI 往往更快一点
- **多轮、要追问、要拿结构化结果**
  桥接方式整体效率更高，因为省我的调度成本
- **长任务**
  两者总时长通常差别不大，Claude 干活时间远大于包装层时间

一句话总结：

**比“纯执行速度”，原生 CLI 略快；比“整体协作效率”，桥接方式通常更高。**

### 增强 Claude bridge 的自动化结果提取

## Features

本skill相对于其他类似skill/协作模式，具有如下重要优势：

1. 使用SOTA的context engineering技术，遵循渐进式披露 (progressive disclosure) 的原则，让codex只需要一次tool call就可以掌握该skill script的使用方法，第二次tool call即可正确调用，无需再搜索/读取该脚本；
2. 兼容各类“在extended thinking开启后会对message结构进行严格校验的” Anthropic-compatible proxy. 
    - 对于某些Anthropic-compatible proxy API, 在thinking启用后，包含工具调用链路的`assistant`消息，需要满足“assistant message 必须以 `thinking/redacted_thinking` 开头，然后才是 `tool_use`，再配套 `tool_result` ……”这类规则。而在print模式下使用claude code时，如果产生上述tool call 链路，`thinking`部分信息会在claude code侧被filtered掉，assistant message会以`tool_use`开头，从而导致router返回400 Error. 而这一问题在claude code交互界面一般不会出现。
    - 针对这一问题，skill中的 bridge script 采取了“把一次长的agentic loop拆成很多次短的loop”的策略：
        - 每次仅允许 claude code 做一次 agentic turn （最多仅一次tool call就调用停止）
        - 然后bridge script 会用相同的session_id自动发送很短的继续指令，让它进行下一步
    - 通过这种方法，可以最大限度地兼容通过各类Anthropic-compatible proxy API运行的claude code.
3. 将claude code的assistant文本实时输出到stderr，便于用户以及codex实时跟踪查看进度。
4. 支持 `--extract-exact`，适合自动化场景下从较长模型回复中严格提取单个标记结果。
5. 在 Windows 下默认尝试隐藏 `claude` 子进程控制台窗口，减少额外弹出的 `cmd` 窗口。

## 安装到 `~/.codex/skills/`

1) 选择一个安装目录（如果不存在就创建）：

```bash
mkdir -p ~/.codex/skills
```

2) 克隆本仓库到 skills 目录下（目录名就是 skill 名）：

```bash
cd ~/.codex/skills
git clone https://github.com/xianzou/collaborating-with-claude-code.git collaborating-with-claude-code
```

3) 验证文件结构（至少应包含 `SKILL.md` 和 `scripts/`）：

```bash
ls -la ~/.codex/skills/collaborating-with-claude-code
```

4) 确认`claude_code_bridge.py`脚本路径：

默认为`~/.codex/skills/collaborating-with-claude-code/scripts/claude_code_bridge.py`. 如果有变动，请在 `SKILL.md`中修改.

测试表明，在 `SKILL.md` 中直接显式声明script的正确路径，会让codex执行bridge script变得更加高效。

完成后，Codex CLI 在加载本地 skills 时就能发现它；在对话中提到 `collaborating-with-claude-code`（或 `$collaborating-with-claude-code`，或自然语言的类似要求）即可触发使用。

## 依赖

- Python 3（用于运行 bridge 脚本）。
- 已安装并可用的 Claude Code CLI（确保 `claude --version` 可运行）。
- Claude Code 已完成认证（例如通过环境变量 `ANTHROPIC_API_KEY`，或你本机 Claude Code 所需的其它认证方式）。

> 注意：该 skill 默认以 **full access** 方式运行 Claude Code（非交互、绕过确认），只建议在你信任的目录/仓库中使用。

## 手动运行（不通过 Codex CLI）

```bash
python <script_loc> --cd "/path/to/repo" --PROMPT "Review the auth flow for bypasses; propose fixes as a unified diff."
```

只读审查（避免改文件/跑命令）：

```bash
python <script_loc> --no-full-access --cd "/path/to/repo" --PROMPT "Review the auth flow and list issues (no code changes)."
```

自动化严格提取单个标记：

```bash
python <script_loc> --no-full-access --cd "/path/to/repo" --extract-exact "OK_MARKER" --PROMPT "Fully understand the repo first. Reply with exactly OK_MARKER."
```

如果 Claude 输出里能找到独立一行的 `OK_MARKER`（允许其余解释文字同时存在），bridge 会仅返回该标记；否则直接返回 `success: false`，避免自动流程误判。

更完整的参数说明与多轮会话用法见 `SKILL.md`。

## 推荐协作方式

- 一个 Claude worker 最好只做一个明确目标，不要混多个子任务。
- 自动调度时，完成信号和自然语言结果应分开处理。
  - 自动化场景优先使用 `--extract-exact "TASK_DONE"` 这类硬标记。
  - 人工 review 场景保留自然语言输出。
- 不要把 bridge 返回的 `success: true` 当成任务验收通过。
  - 这只说明桥接调用成功。
  - 最终仍应由上层主控检查 diff、运行测试并复核结果。

## 运行状态输出（stderr）

- 脚本运行过程中，默认会将 Claude 的 assistant 文本实时输出到 `stderr`（便于看进度），并输出一次 `session_id=...`。
- 最终结构化结果仍只输出到 `stdout`（JSON 不会被 `stderr` 输出污染）。
- 如需关闭所有 `stderr` 输出：`--quiet`

## 兼容性

已经在 codex v0.87, v0.98, v0.101.0，claude code v2.1.11, v2.1.12, v2.1.25, v2.1.104 测试通过。

## License

MIT License，详见 `LICENSE`。
