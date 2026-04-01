# GA4 取数脚本说明

脚本：`scripts/ga4_fuli_report.py`

## 作用
把 GA4 每日数据拉下来，转换成 `dashboard-dual-csv.html` 现在可直接消费的统一 JSON 结构。

当前版本输出：
- 日期
- 总活跃
- 老用户日活（按 总活跃 - 新增 兜底计算）
- 新增
- 次留（暂置 0）
- 3留（暂置 0）
- 7留（暂置 0）
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
- `次留 / 3留 / 7留` 目前没有直接从 GA4 拉，先置 0

## 下一步建议
如果你要和后台日报完全对齐，建议后续继续补：
1. 留存的准确业务口径（人数 / 比例）
2. 留存是走你后台已有聚合结果，还是单独从 GA4 / BigQuery 计算
3. 输出稳定 JSON 给前端直接 fetch
