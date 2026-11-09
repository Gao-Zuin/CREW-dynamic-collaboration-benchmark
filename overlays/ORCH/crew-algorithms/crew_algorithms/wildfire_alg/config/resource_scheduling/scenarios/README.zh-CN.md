# ORCH 事件运行器：火点与待救平民组合

本目录独立于 `focused_tasks.json`、`tasks.json`、`structure_matrix.json` 和 `composite_matrix.json`。`tasks.json` 由 `generate.py` 生成，包含 42 个配置：下面 10 种事件顺序各配 1/2 架无人机、事件地点公开/仅向附近 worker 提示，共 40 个；另有 2 个无新增事件的对照。名称直接写明发生的事、无人机数量和信息方式。

| 事件顺序（坐标，开始步） | 新增工作 |
|---|---|
| `SecondFireAt80_80` | 第 8 步在 (80,80) 起火 |
| `FiveCiviliansAt20_80` | 第 8 步在 (20,80) 增加 5 名待救平民 |
| `SecondFireThenFiveCivilians` | 第 8 步新火点，第 12 步增加 5 名平民 |
| `FiveCiviliansThenSecondFire` | 第 8 步增加 5 名平民，第 12 步新火点 |
| `FireAt80_80ThenFireAt20_80` | 第 8、16 步在两处起火 |
| `FiveCiviliansThenNearbyFire` | 第 8 步增加 5 名平民，第 12 步附近 (20,70) 起火 |
| `OneCivilianAt80_20` | 第 8 步在 (80,20) 增加 1 名平民 |
| `LateFireAt80_80` | 第 16 步在 (80,80) 起火 |
| `SecondFireThenOneCivilian` | 第 8 步新火点，第 12 步增加 1 名平民 |
| `OneCivilianThenTwoFires` | 第 8 步增加 1 名平民，第 12、20 步在两处起火 |

所有配置使用 100×100 Full_Game、原火点、初始 5 名平民、8 名消防员、1 架直升机、1 台推土机和水源。`OneDrone`/`TwoDrones` 改变侦察能力供给。`LocalAlert` 只给组织者不含坐标的火情/平民通知；附近 worker 才收到事件坐标线索，仍须观察后报告。`PublicLocation` 把事件公告中的坐标公开给组织者。配置不预设“必须抢占”：新增工作可能与旧工作竞争，也可能无需改派。事件相同、无人机数相同的两个信息版本可用于比较信息发现的影响。

运行示例：

```bash
SCENARIO=SecondFireThenFiveCivilians_OneDrone_LocalAlert ARM=adaptive SEED=42 bash scripts/run_resource_scenario.sh
```

`ARM=fixed` 使用固定协作边；`ARM=adaptive` 允许改变边。运行器会依据配置自动设置局部/公开事件信息，结果写到 `benchmark_runs/scenarios/`。须使用相同 seed、事件顺序、供给和信息条件配对比较两臂。

## 当前验证边界

配置加载和本地信息遮蔽已做自动检查。2026-11-09 用 seed 42、`SecondFireThenFiveCivilians_OneDrone_PublicLocation` 做 13 步 NOOP Unity 烟测：进程正常结束，运行器在第 8 步记录 `start_fire`、第 12 步记录 `spawn_civilians_5` 提交。此检查没有独立核对新增平民实际数量。此前的物理门禁只覆盖部分第二火点和少量导航路线，不能外推到本目录的平民生成、两次连续事件、100 步内的可解性或任务得分。下一步按研究问题挑选事件后状态检查资源争用、目标可行性、接管与结果。

暂不对 42 个配置逐个做四种子完整策略运行。先保留少量能推翻设计的检查：每类新增事件能在 Unity 生效；局部通知不泄露坐标；同一 seed 两种供给的初始目标可比。只有进入正式比较的实例才追加实际移动、完成时间和分区结果核验。

原生 Full_Game 的 success 主要检查全局灭火，不能单独评价最初/新增平民是否获救，也不能按火点分区评分。因此本批配置目前是**任务候选**，不是已有可解性或组织收益结论；截止时间尚未接入正式评分。
