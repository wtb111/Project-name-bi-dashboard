# GA4 取数脚本说明

脚本：`scripts/ga4_fuli_report.py`

## 作用
把 GA4 每日数据拉下来，转换成 `dashboard-dual-csv.html` 现在可直接消费的统一 JSON 结构。

当前版本输出：
- 日期
- 总活跃
- 老用户日活（按 总活跃 - 新增 兜底计算）
- 新增
- 次留
- 3留
- 7留
- 操作时间

## 依赖
```bash
pip install google-auth
```

## 用法
```bash
python3 scripts/ga4_fuli_report.py \
  --property-id 361679028 \
  --service-account-json /path/to/service-account.json \
  --start-date 2026-03-01 \
  --end-date 2026-03-31 \
  --retention-mode cohort-active-users \
  --pretty
```

输出到文件：
```bash
python3 scripts/ga4_fuli_report.py \
  --property-id 361679028 \
  --service-account-json /path/to/service-account.json \
  --output ./fuli-ga4.json \
  --pretty
```

## 当前口径说明
- `总活跃` = GA4 `activeUsers`
- `新增` = GA4 `newUsers`
- `老用户日活` = `总活跃 - 新增`
- `次留 / 3留 / 7留` 当前支持三种模式：
  - `--retention-mode zero`：全部置 0，最稳
  - `--retention-mode proxy-new-users`：用未来第 N 天 `newUsers` 做临时占位，仅用于前端联调，不代表真实留存口径
  - `--retention-mode cohort-active-users`：按 KNIME 逻辑追加第二条 GA4 查询（date + firstSessionDate + activeUsers）来计算真实留存人数

## 重要提醒
- `proxy-new-users` 只是过渡方案，目的是先把前端趋势图和卡片跑起来。
- `cohort-active-users` 才是按你 KNIME 当前查询思路复刻的版本：
  - Query A: `date + activeUsers + newUsers`
  - Query B: `date + firstSessionDate + activeUsers`
  - 当 `date - firstSessionDate = 1/3/7` 时，分别计入次留/3留/7留人数

## 下一步建议
如果你要和后台日报完全对齐，建议后续继续补：
1. 留存的准确业务口径（人数 / 比例）
2. 留存是走你后台已有聚合结果，还是单独从 GA4 / BigQuery 计算
3. 输出稳定 JSON 给前端直接 fetch
