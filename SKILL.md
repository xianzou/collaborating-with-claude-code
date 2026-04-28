---
name: collaborating-with-claude-code
description: "Delegate code implementation/review/debugging/alternatives to Claude Code via a JSON bridge script. Multi-turn via SESSION_ID."
metadata:
  short-description: Use Claude Code as a collaborator
---

# 版本更新说明
修复了在claude cli@2.1.104中因参数不对，codex会降级直接使用claude cli命令使用的问题(非交互模式，执行完直接输出结果)；
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

# Collaborating with Claude Code

Use this skill for second opinions, code review, test design, or code implementations/alternatives. The bridge runs `claude` (Claude Code) non-interactively ("print" mode) and returns JSON.

The script is located at `~/.codex/skills/collaborating-with-claude-code/scripts/claude_code_bridge.py`.

## Timing

Claude Code often needs **1–2+ minutes** per task.
- Prefer running the bridge directly (no `&`); increase `--timeout-s` as needed (default: 1800s).
- Do **NOT** redirect stdout to a file (e.g. `> /tmp/out.json`).
- By default, the bridge streams Claude's assistant text to `stderr`, and prints only the final JSON envelope to `stdout`.

## Context

- Do **NOT** read the script unless you are modifying it; 
- Before running the script, ALWAYS use `python <script_loc> --help` to get the usage instructions.

## Usage

- please always require claude code to fully understand the codebase before responding or making any changes.
- Put collaborating-with-claude-code terminal commands in the background terminal.
- Always review claude code's responses (or changes it makes) and make sure they are correct, constructive and complete.
- When claude code asks clarifying questions in a multi-turn session, always respond to its questions in that session based on current situation.

## Default

- **full access** (`--full-access`): use only in trusted repos/directories.
- **extended thinking ON** (can disable via `--no-extended-thinking`).
- **step mode AUTO** (can disable via `--step-mode off`).

## Output format

The bridge prints JSON to `stdout`:

```json
{"success": true, "SESSION_ID": "abc123", "agent_messages": "…Claude output…"}
```

## Recommended delegation patterns

- **Guided coding**: "Implement the code for [feature] following these specific steps/constraints."
- **Second opinion**: "Propose an alternative approach and tradeoffs."
- **Code review**: "Find bugs, race conditions, security issues; propose fixes."
- **Test design**: "Write a test plan + edge cases; include example test code."
- **Diff review**: "Review this patch; point out regressions and missing cases."
