from flask import Flask, render_template_string, request

app = Flask(__name__)

# 飼料ライブラリ（成分値は例）
feeds = {
    "乾草": {"TDN": 55, "CP": 10, "NDF": 60},
    "トウモロコシ": {"TDN": 85, "CP": 8, "NDF": 10},
    "配合飼料": {"TDN": 75, "CP": 18, "NDF": 15},
    "アルファルファ乾草": {"TDN": 60, "CP": 18, "NDF": 45},
    "ビートパルプ": {"TDN": 78, "CP": 9, "NDF": 40},
    "大豆粕": {"TDN": 80, "CP": 44, "NDF": 7},
    "ふすま": {"TDN": 70, "CP": 16, "NDF": 38},
    "コーンサイレージ": {"TDN": 70, "CP": 8, "NDF": 45},
    "グラスサイレージ": {"TDN": 60, "CP": 14, "NDF": 55},
    "米ぬか": {"TDN": 75, "CP": 13, "NDF": 20}
}

def calc_nutrient_requirements(milk_kg):
    # 必要エネルギー（TDN, kg/日）の簡易計算式
    tdn = 0.35 * milk_kg + 5.0
    # 必要粗タンパク質（CP, kg/日）の簡易計算式
    cp = 0.09 * milk_kg + 1.2
    return tdn, cp

def feed_design(milk_kg):
    tdn_req, cp_req = calc_nutrient_requirements(milk_kg)
    # 例：乾草2kg, トウモロコシ4kg, 配合飼料3kgで設計
    for hay in range(1, 6):
        for corn in range(1, 8):
            for mix in range(1, 6):
                tdn = (hay * feeds["乾草"]["TDN"] + corn * feeds["トウモロコシ"]["TDN"] + mix * feeds["配合飼料"]["TDN"]) / 100
                cp = (hay * feeds["乾草"]["CP"] + corn * feeds["トウモロコシ"]["CP"] + mix * feeds["配合飼料"]["CP"]) / 100
                if tdn >= tdn_req and cp >= cp_req:
                    return {
                        "乾草": hay,
                        "トウモロコシ": corn,
                        "配合飼料": mix,
                        "TDN": round(tdn, 2),
                        "CP": round(cp, 2),
                        "TDN_req": round(tdn_req, 2),
                        "CP_req": round(cp_req, 2)
                    }
    return None

HTML = """
<!DOCTYPE html>
<html lang=\"ja\">
<head>
    <meta charset=\"UTF-8\">
    <title>酪農用飼料設計</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        table { border-collapse: collapse; }
        th, td { border: 1px solid #888; padding: 0.5em; }
        th { background: #eef; }
        .result { margin-top: 2em; padding: 1em; background: #f8f8f8; border: 1px solid #ccc; }
    </style>
</head>
<body>
    <h1>酪農用飼料設計ツール</h1>
    <form method=\"post\">
        <label>目標乳量 (kg/日): <input type=\"number\" name=\"milk_kg\" step=\"0.1\" required value=\"{{ milk_kg or '' }}\"></label>
        <button type=\"submit\">設計</button>
    </form>
    <h2>飼料ライブラリ</h2>
    <table>
        <tr><th>飼料名</th><th>TDN(%)</th><th>CP(%)</th><th>NDF(%)</th></tr>
        {% for name, comp in feeds.items() %}
        <tr>
            <td>{{ name }}</td>
            <td>{{ comp.TDN }}</td>
            <td>{{ comp.CP }}</td>
            <td>{{ comp.NDF }}</td>
        </tr>
        {% endfor %}
    </table>
    {% if result %}
    <div class=\"result\">
        <h3>設計例</h3>
        <ul>
            <li>乾草: {{ result['乾草'] }} kg</li>
            <li>トウモロコシ: {{ result['トウモロコシ'] }} kg</li>
            <li>配合飼料: {{ result['配合飼料'] }} kg</li>
        </ul>
        <p>→ 合計TDN: {{ result['TDN'] }} kg（必要: {{ result['TDN_req'] }} kg）<br>
        合計CP: {{ result['CP'] }} kg（必要: {{ result['CP_req'] }} kg）</p>
    </div>
    {% elif milk_kg %}
    <div class=\"result\">
        <p>適切な飼料配分が見つかりませんでした。</p>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    milk_kg = None
    result = None
    if request.method == 'POST':
        try:
            milk_kg = float(request.form['milk_kg'])
            result = feed_design(milk_kg)
        except Exception:
            milk_kg = None
    return render_template_string(HTML, feeds=feeds, result=result, milk_kg=milk_kg)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')