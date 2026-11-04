import plotly.graph_objects as go
from plotly.io import to_html
import pandas as pd


def generate_index_html(result: dict, output_path: str):
    """
    将模型预测结果渲染为静态 HTML 报告
    """
    # --- 1. 生成 K线图 (示例) ---
    fig_kline = go.Figure(data=[go.Candlestick(
        x=result['kline_df'].index,
        open=result['kline_df']['open'], high=result['kline_df']['high'],
        low=result['kline_df']['low'], close=result['kline_df']['close']
    )])
    fig_kline.update_layout(title='上证指数历史走势', height=400)
    kline_html = to_html(fig_kline, full_html=False, include_plotlyjs='cdn')

    # --- 2. 生成特征重要性图 (示例) ---
    fig_imp = go.Figure(data=[go.Bar(
        x=result['feature_importance']['importance'],
        y=result['feature_importance']['feature']
    )])
    fig_imp.update_layout(title='模型特征重要性 TOP 15', height=400)
    imp_html = to_html(fig_imp, full_html=False, include_plotlyjs='cdn')

    # --- 3. 组装完整的 HTML ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>上证择时信号日报</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f4f4f9; padding: 20px; color: #333; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .signal {{ display: inline-block; padding: 10px 20px; border-radius: 8px; color: white; font-size: 20px; font-weight: bold; margin-bottom: 20px; }}
            .bullish {{ background: #e74c3c; }} .bearish {{ background: #2ecc71; }}
            .chart-box {{ margin-top: 20px; border: 1px solid #eee; border-radius: 8px; padding: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 上证择时 XGBoost 信号</h1>
            <p style="color: #666; font-size: 14px;">更新时间：{result['update_time']}</p>

            <div class="signal {'bullish' if result['direction'] == '看涨' else 'bearish'}">
                当前信号：{result['direction']} (概率: {result['prob']:.2%})
            </div>

            <div class="chart-box">{kline_html}</div>
            <div class="chart-box">{imp_html}</div>
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)