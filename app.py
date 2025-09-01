import os
from dotenv import load_dotenv
from arcgis.gis import GIS
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

# 載入 .env 檔案中的環境變數
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    return "Hello, World! 我的 GIS API 使用帳號密碼進行驗證。"

@app.route("/api/time-difference", methods=['POST', 'OPTIONS', 'GET'])
def time_difference_analysis():
    try:
        if request.method == 'OPTIONS':
            return '', 204
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "請求中未包含 JSON 資料"}), 400
        
        # 從 JSON 中取得前端傳來的兩個 Item ID
        item_id_1 = data.get('itemId1')
        item_id_2 = data.get('itemId2')

        if not item_id_1 or not item_id_2:
            return jsonify({"error": "請求中缺少 itemId1 或 itemId2 參數"}), 400

        # 1. 從環境變數讀取 ArcGIS Online 的帳號和密碼
        username = os.getenv("ARCGIS_USERNAME")
        password = os.getenv("ARCGIS_PASSWORD")

        if not username or not password:
            raise ValueError("找不到 ARCGIS_USERNAME 或 ARCGIS_PASSWORD，請檢查 .env 檔案")
        
        # 2. 使用帳號密碼登入 ArcGIS Online
        gis = GIS("https://igisportal.geomatics.ncku.edu.tw/portal/", username=username, password=password)
        print(f"成功以使用者 '{username}' 的身份登入 ArcGIS Online...")


        # 3. 透過 Item ID 取得圖層

        item_1 = gis.content.get(item_id_1)
        item_2 = gis.content.get(item_id_2)

        layer_1 = item_1.layers[0]
        layer_2 = item_2.layers[0]

        # 4. 查詢圖層資料並轉換為 Spatially Enabled DataFrame
        sdf_1 = layer_1.query().df
        sdf_2 = layer_2.query().df
        print("成功從 ArcGIS Online 取得圖層資料...")

        # 5. 執行分析
        #sdf_1 = sdf_1.rename(columns={'p_cnt': 'POP_1', 'info_time': 'year1'})
        #sdf_2 = sdf_2.rename(columns={'p_cnt': 'POP_2', 'info_time': 'year2'})
        sdf_1 = sdf_1.rename(columns={'info_time': 'year1'})
        sdf_2 = sdf_2.rename(columns={'info_time': 'year2'})

        if int(sdf_1['year1'][0].split('Y')[0]) > int(sdf_2['year2'][0].split('Y')[0]):
            newer_layer = sdf_1
            older_layer = sdf_2

            newer_layer = newer_layer.rename(columns={'p_cnt': 'POP_newer', 'year1': 'year_newer'})
            older_layer = older_layer.rename(columns={'p_cnt': 'POP_older', 'year2': 'year_older'})
        else:
            newer_layer = sdf_2
            older_layer = sdf_1

            newer_layer = newer_layer.rename(columns={'p_cnt': 'POP_newer', 'year2': 'year_newer'})
            older_layer = older_layer.rename(columns={'p_cnt': 'POP_older', 'year1': 'year_older'})
        print("時間判斷成功...")
        
        newer_simple = newer_layer[['villcode', 'village', 'POP_newer', 'year_newer', 'SHAPE']]
        older_simple = older_layer[['villcode', 'village', 'POP_older', 'year_older']]
        
        diff_sdf = newer_simple
        diff_sdf['year_older'] = older_simple['year_older']
        diff_sdf['POP_older'] = older_simple['POP_older']
        diff_sdf['POP_DIFF'] = newer_simple['POP_newer'] - older_simple['POP_older']
        print("資料分析運算完成...")

        # 6. 將結果轉換為 GeoJSON 並回傳
        result_geojson = diff_sdf.to_json(orient="records")
        
        return Response(result_geojson, mimetype='application/json')

    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)