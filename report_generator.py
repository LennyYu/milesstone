"""
报告生成器 - 读取XGBoost预测结果CSV，生成Plotly交互式HTML报告
放置位置：仓库根目录 (milesstone/) 或 pythonProject/ 目录下均可
执行后自动生成 docs/index.html
"""
import os
import sys
import pandas as pd
from datetime import datetime

try:
    import plotly.graph_objects as go
    from plotly.io import to_html
except ImportError:
    print("缺少plotly，请执行: pip install plotly")
    sys.exit(1)


def generate_report():
    """读取预测结果并生成HTML报告"""

    # ===== 路径配置 =====
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 尝试多种路径策略定位数据目录
    data_dir = os.path.join(script_dir, "行情数据")

    if not os.path.exists(data_dir):
        data_dir = os.path.join(os.path.dirname(script_dir), "行情数据")

    if not os.path.exists(data_dir):
        project_root = os.path.dirname(script_dir)
        data_dir = os.path.join(project_root, "行情数据")

    result_csv = os.path.join(data_dir, "预测结果_近期.csv")
    stock_csv = os.path.join(data_dir, "上证指数行情数据.csv")

    # 定位仓库根目录（用于写入 docs/index.html）
    if os.path.exists(os.path.join(script_dir, "docs")):
        repo_root = script_dir
    else:
        parent = os.path.dirname(script_dir)
        if os.path.exists(os.path.join(parent, "docs")):
            repo_root = parent
        else:
            repo_root = os.path.join(script_dir, "milesstone")
            if not os.path.exists(os.path.join(repo_root, "docs")):
                repo_root = script_dir

    # ===== 读取数据 =====
    df_pred = pd.read_csv(result_csv)
    df_stock = pd.read_csv(stock_csv)
    df_stock["time"] = pd.to_datetime(df_stock["time"])

    # 获取最新预测（最后一行是"明天"预测）
    latest = df_pred.iloc[-1]
    prob = latest["预测上涨概率"]
    direction = latest["预测方向"]
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ===== 生成图表 =====

    # 图表1: K线图（最近120天）
    recent_days = 120
    df_recent = df_stock.tail(recent_days).copy()

    fig_kline = go.Figure(data=[go.Candlestick(
        x=df_recent["time"],
        open=df_recent["open"],
        high=df_recent["high"],
        low=df_recent["low"],
        close=df_recent["close"],
        name="价格"
    )])
    fig_kline.update_layout(
        title="上证指数近期走势",
        height=400,
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        xaxis_title="日期",
        yaxis_title="价格",
        margin=dict(l=10, r=10, t=40, b=10)
    )
    kline_html = to_html(fig_kline, full_html=False, include_plotlyjs="cdn")

    # 图表2: 预测上涨概率趋势
    fig_prob = go.Figure()
    fig_prob.add_trace(go.Scatter(
        x=list(range(len(df_pred))),
        y=df_pred["预测上涨概率"].values,
        mode="lines+markers",
        name="上涨概率",
        marker=dict(size=5)
    ))
    fig_prob.add_hline(
        y=0.5, line_dash="dash", line_color="gray",
        annotation_text="阈值 0.5", annotation_position="top right"
    )
    fig_prob.update_layout(
        title="预测上涨概率趋势",
        xaxis_title="交易日序号",
        yaxis_title="概率",
        height=350,
        template="plotly_white",
        margin=dict(l=10, r=10, t=40, b=10)
    )
    prob_html = to_html(fig_prob, full_html=False, include_plotlyjs="cdn")

    # 图表3: 特征重要性（如果CSV中有对应文件）
    importance_html = ""
    importance_csv = os.path.join(data_dir, "特征重要性.csv")
    if os.path.exists(importance_csv):
        df_imp = pd.read_csv(importance_csv)
        fig_imp = go.Figure(data=[go.Bar(
            x=df_imp["importance"].values,
            y=df_imp["feature"].values,
            orientation="h"
        )])
        fig_imp.update_layout(
            title="模型特征重要性 TOP 15",
            height=350,
            template="plotly_white",
            xaxis_title="重要性",
            yaxis_title="特征",
            margin=dict(l=10, r=10, t=40, b=10)
        )
        importance_html = to_html(fig_imp, full_html=False, include_plotlyjs="cdn")

    # ===== 组装表格HTML =====
    table_rows = ""
    for _, row in df_pred.iterrows():
        date_val = row.get("日期", "")
        close_val = row.get("收盘价", "")
        if pd.isna(close_val):
            close_val = ""
        else:
            close_val = "{:.2f}".format(float(close_val))
        actual_val = row.get("次日实际涨跌", "")
        if pd.isna(actual_val):
            actual_val = ""
        prob_val = row.get("预测上涨概率", "")
        if pd.isna(prob_val):
            prob_val = ""
        else:
            prob_val = "{:.4f}".format(float(prob_val))
        pred_dir = row.get("预测方向", "")
        if pd.isna(pred_dir):
            pred_dir = ""

        table_rows += """
        <tr>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
        </tr>""".format(date_val, close_val, actual_val, prob_val, pred_dir)

    # ===== 信号样式 =====
    if direction in ("看涨",):
        signal_class = "bullish"
        signal_color = "#e74c3c"
        signal_text = "看涨"
    elif direction in ("看跌",):
        signal_class = "bearish"
        signal_color = "#2ecc71"
        signal_text = "看跌"
    else:
        signal_class = "neutral"
        signal_color = "#95a5a6"
        signal_text = str(direction)

    # ===== 组装完整HTML =====
    imp_box = ""
    if importance_html:
        imp_box = '<div class="chart-box">{}</div>'.format(importance_html)

    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>上证择时信号日报</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            background: #f0f2f5;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #fff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        h1 {{
            font-size: 24px;
            margin-bottom: 8px;
            color: #1a1a2e;
        }}
        .subtitle {{
            color: #888;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .signal-badge {{
            display: inline-block;
            padding: 10px 24px;
            border-radius: 8px;
            color: #fff;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 24px;
            background-color: {signal_color};
        }}
        .chart-box {{
            margin-top: 24px;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            padding: 12px;
            background: #fafafa;
        }}
        .chart-box h3 {{
            font-size: 16px;
            margin-bottom: 12px;
            color: #555;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 24px;
            font-size: 14px;
        }}
        th, td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e8e8e8;
            text-align: center;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
            position: sticky;
            top: 0;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e8e8e8;
            color: #aaa;
            font-size: 12px;
            text-align: center;
        }}
        @media (max-width: 600px) {{
            .container {{ padding: 16px; }}
            table {{ font-size: 12px; }}
            th, td {{ padding: 6px 8px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>上证择时 XGBoost 信号日报</h1>
        <p class="subtitle">数据更新时间：{update_time}</p>

        <div class="signal-badge">{signal_text} (概率: {prob:.2%})</div>

        <div class="chart-box">{kline_html}</div>
        <div class="chart-box">{prob_html}</div>
        {imp_box}

        <h3 style="margin-top:24px; color:#555;">预测结果明细</h3>
        <div style="overflow-x:auto;">
        <table>
            <thead>
                <tr>
                    <th>日期</th>
                    <th>收盘价</th>
                    <th>次日实际涨跌</th>
                    <th>预测上涨概率</th>
                    <th>预测方向</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        </div>

        <div class="footer">
            由 auto_update.py 自动定时生成 | 基于 XGBoost 模型预测
        </div>
    </div>
</body>
</html>""".format(
        signal_color=signal_color,
        signal_text=signal_text,
        update_time=update_time,
        prob=float(prob),
        kline_html=kline_html,
        prob_html=prob_html,
        imp_box=imp_box,
        table_rows=table_rows
    )

    # ===== 保存到 docs/index.html =====
    output_path = os.path.join(repo_root, "docs", "index.html")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("报告已生成: {}".format(output_path))
    print("文件大小: {} bytes".format(os.path.getsize(output_path)))
    return output_path


if __name__ == "__main__":
    generate_report()
