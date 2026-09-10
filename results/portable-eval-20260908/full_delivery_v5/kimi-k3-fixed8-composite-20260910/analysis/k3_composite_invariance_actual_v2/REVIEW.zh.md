# 最终K3 composite：原严格不变量通过

实际独立执行6976e3 exit0；对象仅为 `../actual_k3_fixed8_composite_export_v2_py311_final`。
EXPORT_INDEX SHA `fc68a5a057c45056924b17b91f054311d6cd43dc8174da85892265f8d7758f86`；exact18文件、75,085,881B已逐文件SHA/bytes/stat验证。
按原BASELINE `d3719a4cc74d36a46b0f0ee72570de9cac877484ab051f995f95698274aa90dc`，没有修改允许集合或增加容差。

## 严格结论

- 341个不受固定8影响的效应**所有字段精确相同**；另11个允许范围内也不变，故352整行相同。
- 实际改变162行，全部在预定173允许集合内，均从old unknown变为完整endpoint；比较分母/CI规则没有新增。
- 五个原已知主效应和23个旧负性能整行精确保留；六主仅E-H可变化，未要求变化方向必须正。
- 原manifest逐字节相同；783 logical中非fixed8的775条完整records精确相同，7588条非fixed8 metric行精确相同。
- 有效来源严格原697+指定新8，705 invocation / 783 logical / 1881 agent slots；完整Pool来源不混新旧，物理attempt713不充当额外统计样本。
- 2247 source_index及rich source map来源/sha/segment/IID/ordinal互绑；全部514效应CI/p仍null。
- old16320+new289=16609 persisted request，联合run_id/request_id无重复；旧path→SHA、request ID与IID集合全部保留，old16257success+63error、新289success，与各段原closure计数一致。
- 三字段逐request独立加总：input known=126,556,991，output known=16,272,997，reasoning known=13,992,686；各保留63个旧unknown，complete_total仍null。reasoning不相加，供应商/分配GPU账单未知。
- 新289与独立usage作者的实际原raw核验逐request对账精确；新8的28个性能metric cell与另一原26结果/Gap算术复核全部delta0。

## 旧失败不隐藏

Python3.10首次18输出与 `../k3_composite_invariance_actual_v1` 的strict失败原样保留：18行SD各差1ULP，不满足341所有字段精确要求。
同原outer triples已分别在Python3.10/3.11标准库精确复现；ROOT另用原K3匹配3.11解释器和未改merge生成此fresh版本。
本次没有靠放宽阈值通过，也没有重跑任何模型。GLM公共回放自己的解释器pin独立保留，不能以跨模型环境统一替代各自版本可重现性。

## 边界

本程序仅读取冻结export/control/closure与独立科学审查的产物，不运行模型、原scorer、backend、AN2或merge；旧raw正文没有再次读取。
旧费用部分为原accepted sidecar/closure与ledger的完整metadata对账；新289原raw由独立usage作者已实际检查并另留证据。
341效应/775 records/7588 rows均是精确比较；新独立算术使用显式1e-12浮点比较且实际28项delta全0，不混为严格不变量容差。
这是数据输出后的独立有限审查，**不是最终报告冻结后的审查**；不能由六主方向推断所有次要指标、模型或场景普适改善。STOP-WRITE随INDEX生效。
