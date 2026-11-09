# ORCH 事件运行器：火点与待救平民组合

本目录独立于 `focused_tasks.json`、`tasks.json`、`structure_matrix.json` 和 `composite_matrix.json`。`tasks.json` 由 `generate.py` 生成，包含 42 个配置：下面 10 种事件顺序各配 1/2 架无人机、完整事件先给组织者/先给一名 worker，共 40 个；另有 2 个无新增事件的对照。名称直接写明发生的事、无人机数量和信息方式。

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

所有配置使用 100×100 Full_Game、原火点、初始 5 名平民、8 名消防员、1 架直升机、1 台推土机和水源。`OneDrone`/`TwoDrones` 改变侦察能力供给。`OrganizerDirect` 将包含坐标的官方事件通知直接提供给组织者，随后由组织者向 worker 下发。`WorkerReport` 将同一通知只交给一名 worker：火点优先选无人机，平民优先选消防员；在对应类型中优先选非组长，再按距离选最近者。**没有 10 格半径限制**，因此远处火点也能被接收，但地点必须由该 worker 经组长上报到组织者。收到官方报告仍不能当作目标当前状态的直接观测。配置不预设“必须抢占”：新增工作可能与旧工作竞争，也可能无需改派。事件相同、无人机数相同的两个信息版本可用于比较信息传递路径的影响。

人数是从原版 `Full_Game` 的职业种类和原版灭火/救援任务的需求出发，为 100×100 复合场景人工缩减和配对的配置，并非从轨迹中推断出的最低可行人数。原版 `Full_Game` 为 10 消防员、2 无人机、2 直升机、1 推土机；本目录固定 8 消防员、1 直升机、1 推土机，只改变无人机为 1/2 架。因而本目录没有直升机 1/2 架的容量对照；旧 `focused_tasks.json` 有该对照，但两组是否真的同时需要直升机仍须用轨迹验证。

运行示例：

```bash
SCENARIO=SecondFireThenFiveCivilians_OneDrone_WorkerReport ARM=adaptive SEED=42 bash scripts/run_resource_scenario.sh
```

`ARM=fixed` 使用固定协作边；`ARM=adaptive` 允许改变边。运行器会依据配置自动设置局部/公开事件信息，结果写到 `benchmark_runs/scenarios/`。须使用相同 seed、事件顺序、供给和信息条件配对比较两臂。

## 当前验证边界

配置加载、`WorkerReport` 只发给 worker、不直接进入组织者决策状态，及无半径门槛的远处消息投递已做自动检查。2026-11-09 用 seed 42、当时名为 `SecondFireThenFiveCivilians_OneDrone_PublicLocation` 的事件内容做 13 步 NOOP Unity 烟测：进程正常结束，运行器在第 8 步记录 `start_fire`、第 12 步记录 `spawn_civilians_5` 提交；该配置随后更名为 `SecondFireThenFiveCivilians_OneDrone_OrganizerDirect`，事件命令未变。此检查没有独立核对新增平民实际数量，也未用 LLM 跑通 worker→组长→组织者的上报链。此前的物理门禁只覆盖部分第二火点和少量导航路线，不能外推到本目录的平民生成、两次连续事件、100 步内的可解性或任务得分。下一步按研究问题挑选事件后状态检查资源争用、目标可行性、接管与结果。

暂不对 42 个配置逐个做四种子完整策略运行。先保留少量能推翻设计的检查：每类新增事件能在 Unity 生效；WorkerReport 不把官方事件直接交给组织者；同一 seed 两种供给的初始目标可比。只有进入正式比较的实例才追加实际上报、移动、完成时间和分区结果核验。

原生 Full_Game 的 success 主要检查全局灭火，不能单独评价最初/新增平民是否获救，也不能按火点分区评分。因此本批配置目前是**任务候选**，不是已有可解性或组织收益结论；截止时间尚未接入正式评分。
