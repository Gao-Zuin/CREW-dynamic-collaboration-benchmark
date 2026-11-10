# 原火组推土机开工后：新增五名平民，再出现附近火点

仅有两个信息版本，物理事件相同：

| 配置名 | 官方事件先交给谁 |
|---|---|
| `FiveCiviliansAt80_75AfterOriginalFireDozerMovesThenFireAt80_80_WorkerReport` | 一名现场消防员，经组长上报组织者 |
| `FiveCiviliansAt80_75AfterOriginalFireDozerMovesThenFireAt80_80_OrganizerDirect` | 组织者 LLM |

固定 8 名消防员、1 台推土机、1 架无人机、1 架直升机、初始 5 名平民和原火。第 8 步起，只有观察到**当前仍属于原火组的推土机执行了一次有位移的动作**、原火仍活跃、初始获救人数不足 5，才提交位于 `(80,75)` 的新增 5 人事件。推土机运动只作为“旧工作已开始”的代理，不代表隔离带已建成。若到第 18 步条件仍不成立，事件回退提交，并标记 `fallback_latest_timestep`；这种运行**不计入承诺状态触发组**。新增火点 `(80,80)` 在前一事件实际提交后第 6 步出现。

运行入口：

```bash
SCENARIO_FAMILY=commitment_event \
SCENARIO=FiveCiviliansAt80_75AfterOriginalFireDozerMovesThenFireAt80_80_WorkerReport \
ARM=adaptive SEED=42 MODEL=deepseek-v4-flash MAX_STEPS=32 \
CREW_HT_PARALLEL_MODEL_CALLS=1 CREW_HT_MODEL_WORKERS=8 \
bash scripts/run_resource_scenario.sh
```

`deepseek-v4-flash` 是 API 请求名；2026-11-10 用官方 DeepSeek `/models` 与一次小请求核对，该请求响应的 `model` 字段为 `deepseek-flash`。根据官方更新说明，旧 V4 Flash 名称已路由到当前 Flash，不能把本实验称为冻结的旧版 V4 权重结果。每次正式运行需保存请求名、响应模型名和日期。
worker 与组织者两个独立调用路径都对这个别名显式发送 `thinking: disabled`；否则旧前缀判断无法命中，会额外产生大量思考 token，并可能使组织者的 JSON 响应在 token 上限处截断。正式结果见 [RESULTS.zh-CN.md](RESULTS.zh-CN.md)。

可选的同一步模型调用并行只在 HT 且 `CREW_HT_ROUND_DELIVERY=1` 时启用。同一步 worker 消息原本就要等下一步才送达，故感知、消息生成和动作提案可分别并行；环境动作提交、图更新与下一步投递仍顺序执行。运行记录标注该选项，不能与串行通信实验无标注混合比较。

分析：`python scripts/analyze_commitment_event_run.py <RUN_LOG_ROOT>/events.jsonl`。结果按事件分列释放原因、首次上报、首次改组及动作命令；动作命令不等于 Unity 物理效果。分区火势、新增平民实体数、新增平民获救数仍为空值，需后续独立仪表或 worker 新鲜视野核对。
组长通信提示现要求：收到 worker `REPORT` 中的新信息后，用 `ORGANIZER` 上报组织者，注明来源与是否亲眼证实；重复且未变化的状态不用反复发送。`RESULTS.zh-CN.md` 中的 26 步轨迹采集于该提示修改之前，不能用来判断修改后的上报率。
分析器还从事件释放时各职业的位置给出到新目标的欧氏距离和**理想最短移动步数**。消防员、推土机、无人机、直升机分别按每步最多 12、8、20、30 格估计；地形减速、消息传递、交互动作会让实际时间更长。

## 已做的最小门禁

- 纯函数与运行桥测试：条件未成立时不能提前释放；实际释放步数决定后续火点时间；推土机必须有返回环境的位移；初始平民已全救时不算条件成立。
- seed 42 的 26 步 Unity NOOP：无推土机承诺，第 18 步回退提交平民，第 24 步提交火点，各一次，正常结束。
- 同配置 seed 42 的 12 步 Unity NOOP 火势核验：`fire_active` 在第 0–2 步为假，第 3–11 步为真，说明前期为启动延迟；第 8 步累计烧毁树木数为 2。
- 这些检查没有验证新增平民实体、推土机清树、平民救援或重组收益。正式纳入 benchmark 需补事件后可行性、分区结果与同状态 fixed/adaptive 配对。
