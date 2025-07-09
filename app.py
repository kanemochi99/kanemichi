from flask import Flask, render_template_string, request
from scipy.optimize import linprog

app = Flask(__name__)

# 飼料ライブラリ（成分値・単価は例）
feeds = {
    "乾草": {"TDN": 55, "CP": 10, "NDF": 60, "price": 40},
    "トウモロコシ": {"TDN": 85, "CP": 8, "NDF": 10, "price": 50},
    "配合飼料": {"TDN": 75, "CP": 18, "NDF": 15, "price": 60},
    "アルファルファ乾草": {"TDN": 60, "CP": 18, "NDF": 45, "price": 70},
    "ビートパルプ": {"TDN": 78, "CP": 9, "NDF": 40, "price": 55},
    "大豆粕": {"TDN": 80, "CP": 44, "NDF": 7, "price": 90},
    "ふすま": {"TDN": 70, "CP": 16, "NDF": 38, "price": 45},
    "コーンサイレージ": {"TDN": 70, "CP": 8, "NDF": 45, "price": 30},
    "グラスサイレージ": {"TDN": 60, "CP": 14, "NDF": 55, "price": 25},
    "米ぬか": {"TDN": 75, "CP": 13, "NDF": 20, "price": 50}
}

feed_names = list(feeds.keys())

HTML = """
<!DOCTYPE html>
<html lang=\"ja\">
<head>
    <meta charset=\"UTF-8\">
    <title>酪農用飼料設計（最適化）</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        table { border-collapse: collapse; }
        th, td { border: 1px solid #888; padding: 0.5em; }
        th { background: #eef; }
        .result { margin-top: 2em; padding: 1em; background: #f8f8f8; border: 1px solid #ccc; }
        .input-table input { width: 5em; }
    </style>
</head>
<body>
    <h1>酪農用飼料設計ツール（最適化）</h1>
    <form method=\"post\">
        <label>目標乳量 (kg/日): <input type=\"number\" name=\"milk_kg\" step=\"0.1\" required value=\"{{ milk_kg or '' }}\"></label>
        <h2>飼料選択・上限・単価</h2>
        <table class=\"input-table\">
            <tr><th>使う</th><th>飼料名</th><th>最大給与量(kg)</th><th>単価(円/kg)</th><th>TDN(%)</th><th>CP(%)</th><th>NDF(%)</th></tr>
            {% for name in feed_names %}
            <tr>
                <td><input type=\"checkbox\" name=\"use_{{ name }}\" {% if use_feeds and use_feeds[name] %}checked{% endif %}></td>
                <td>{{ name }}</td>
                <td><input type=\"number\" name=\"max_{{ name }}\" step=\"0.1\" min=\"0\" value=\"{{ max_feeds[name] }}\"></td>
                <td><input type=\"number\" name=\"price_{{ name }}\" step=\"1\" min=\"0\" value=\"{{ prices[name] }}\"></td>
                <td>{{ feeds[name][\"TDN\"] }}</td>
                <td>{{ feeds[name][\"CP\"] }}</td>
                <td>{{ feeds[name][\"NDF\"] }}</td>
            </tr>
            {% endfor %}
        </table>
        <button type=\"submit\">最適設計</button>
    </form>
    {% if result %}
    <div class=\"result\">
        <h2>設計結果</h2>
        <table>
            <tr><th>飼料名</th><th>給与量(kg)</th></tr>
            {% for name, kg in result['配分'].items() %}
            <tr><td>{{ name }}</td><td>{{ kg }}</td></tr>
            {% endfor %}
        </table>
        <p>合計TDN: {{ result['TDN'] }} kg（必要: {{ result['TDN_req'] }} kg）<br>
        合計CP: {{ result['CP'] }} kg（必要: {{ result['CP_req'] }} kg）<br>
        合計NDF: {{ result['NDF'] }} kg<br>
        合計コスト: {{ result['cost'] }} 円</p>
    </div>
    {% elif error %}
    <div class=\"result\"><b style=\"color:red\">{{ error }}</b></div>
    {% endif %}
</body>
</html>
"""

def calc_nutrient_requirements(milk_kg):
    tdn = 0.35 * milk_kg + 5.0
    cp = 0.09 * milk_kg + 1.2
    ndf = 0.25 * milk_kg + 3.0  # 仮のNDF目標
    return tdn, cp, ndf

def optimize_feeds(milk_kg, use_feeds, max_feeds, prices):
    tdn_req, cp_req, ndf_req = calc_nutrient_requirements(milk_kg)
    selected = [i for i, name in enumerate(feed_names) if use_feeds[name]]
    if not selected:
        return None, '1つ以上の飼料を選択してください。'
    # 目的関数: コスト最小化
    c = [prices[feed_names[i]] for i in selected]
    # 各飼料の成分
    tdn = [feeds[feed_names[i]]["TDN"] / 100 for i in selected]
    cp = [feeds[feed_names[i]]["CP"] / 100 for i in selected]
    ndf = [feeds[feed_names[i]]["NDF"] / 100 for i in selected]
    # 制約: 成分が必要量以上
    A = [
        [-x for x in tdn],   # -sum >= -tdn_req → sum >= tdn_req
        [-x for x in cp],
        [-x for x in ndf]
    ]
    b = [-tdn_req, -cp_req, -ndf_req]
    # 上限
    bounds = [(0, float(max_feeds[feed_names[i]])) for i in selected]
    res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method='highs')
    if res.success:
        配分 = {feed_names[i]: round(res.x[j], 2) for j, i in enumerate(selected)}
        total_tdn = sum(res.x[j] * tdn[j] for j in range(len(selected)))
        total_cp = sum(res.x[j] * cp[j] for j in range(len(selected)))
        total_ndf = sum(res.x[j] * ndf[j] for j in range(len(selected)))
        total_cost = sum(res.x[j] * c[j] for j in range(len(selected)))
        return {
            '配分': 配分,
            'TDN': round(total_tdn, 2),
            'CP': round(total_cp, 2),
            'NDF': round(total_ndf, 2),
            'cost': round(total_cost),
            'TDN_req': round(tdn_req, 2),
            'CP_req': round(cp_req, 2),
            'NDF_req': round(ndf_req, 2)
        }, None
    else:
        return None, '条件を満たす飼料配分が見つかりませんでした。'

@app.route('/', methods=['GET', 'POST'])
def index():
    milk_kg = None
    result = None
    error = None
    # デフォルト値
    use_feeds = {name: True for name in feed_names}
    max_feeds = {name: 5.0 for name in feed_names}
    prices = {name: feeds[name]['price'] for name in feed_names}
    if request.method == 'POST':
        try:
            milk_kg = float(request.form['milk_kg'])
            for name in feed_names:
                use_feeds[name] = f'use_{name}' in request.form
                max_feeds[name] = float(request.form.get(f'max_{name}', 0) or 0)
                prices[name] = float(request.form.get(f'price_{name}', 0) or 0)
            result, error = optimize_feeds(milk_kg, use_feeds, max_feeds, prices)
        except Exception as e:
            error = f'入力エラー: {e}'
    return render_template_string(HTML, feeds=feeds, feed_names=feed_names, milk_kg=milk_kg, use_feeds=use_feeds, max_feeds=max_feeds, prices=prices, result=result, error=error)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')