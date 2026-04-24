---
name: karpathy-guidelines
description: Use when starting any task - think before coding, keep solutions simple, make surgical changes, and decide which project skills should be loaded next
---

# Karpathy Guidelines

在开始任何任务前，先按下面四条原则校准工作方式，再决定是否需要加载其他项目 skills。

## 1. Think Before Coding

- 先明确目标、约束、影响范围，再动手。
- 如果问题本质上是调查、规划、排障或验证，先进入对应流程，不要直接改代码或改文档。
- 任何时候只要觉得任务可能需要其他 skill，就先加载 skill，再继续。

## 2. Simplicity First

- 优先选最简单、最直接、最容易验证的方案。
- 不为了“更通用”“更优雅”而引入当前任务并不需要的复杂度。
- 文档与说明也保持最小必要改动，避免顺手重写无关部分。

## 3. Surgical Changes

- 只改与目标直接相关的文件和段落。
- 保持已有结构、命名和约束一致，除非本次任务明确要求迁移。
- 如果必须改动工作流入口，要同步更新所有引用它的仓库说明，避免留下断链。

## 4. Goal-Driven Execution

- 始终围绕“什么证据能证明任务完成”来推进。
- 在执行前判断是否应加载以下项目 skills：
  - `planning-with-files`：复杂多步骤任务、长链路调查、跨多文件改动
  - `test-driven-development`：功能、行为变化、bugfix、重构
  - `systematic-debugging`：异常、测试失败、构建失败、联机问题
  - `verification-before-completion`：任何准备对外宣称完成、修复、通过的时刻

## 本项目中的使用方式

默认顺序：

1. 先读 `CLAUDE.md` 和 `README.md`
2. 再读本文件，确认本次任务的目标、边界和最小改动路径
3. 根据任务类型按需加载其他项目 skills
4. 收尾前必须走 `verification-before-completion`

## 快速自检

开始执行前，至少确认这四件事：

1. 我是不是已经理解了真正目标，而不是只盯着表面动作？
2. 我选的是不是当前最简单可验证的方案？
3. 我会不会误改无关文件，或者留下新的引用断链？
4. 我有没有加载这次任务真正需要的项目 skill？
