import os
from dotenv import load_dotenv
from arcgis.gis import GIS
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

load_dotenv() 

# 1. 從環境變數讀取 ArcGIS Online 的帳號和密碼
username = os.getenv("ARCGIS_USERNAME")
password = os.getenv("ARCGIS_PASSWORD")

if not username or not password:
    raise ValueError("FATAL ERROR: Environment variables not set.")

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
        print("從前端取得資料")
        if not data:
            return jsonify({"error": "請求中未包含 JSON 資料"}), 400

        # 比較圖層時間新舊
        layer1_info = data.get('itemId1')
        layer2_info = data.get('itemId2')
        if not layer1_info or not layer2_info:
            return jsonify({"error": "請求中缺少 itemId1 或 itemId2 參數"}), 400

        if layer1_info['year'] > layer2_info['year']:
            newer_layer_info = layer1_info
            older_layer_info = layer2_info
        else:
            newer_layer_info = layer2_info
            older_layer_info = layer1_info
        print("完成時間比較")
        
        # 從 JSON 中取得前端傳來的兩個 Item ID
        item_newer_id = newer_layer_info['id']
        item_older_id = older_layer_info['id']
        
        # 2. 使用帳號密碼登入 ArcGIS Online
        gis = GIS("https://igisportal.geomatics.ncku.edu.tw/portal/", username=username, password=password)
        print(f"成功以使用者 '{username}' 的身份登入 ArcGIS Online...")

        # 3. 透過 Item ID 取得圖層
        item_newer = gis.content.get(item_newer_id)
        item_older = gis.content.get(item_older_id)

        layer_newer = item_newer.layers[0]
        layer_older = item_older.layers[0]

        # 4. 查詢圖層資料並轉換為 Spatially Enabled DataFrame
        sdf_1 = layer_newer.query().df
        sdf_2 = layer_older.query().df
        print("成功從 ArcGIS Online 取得圖層資料...")

        # 5. 執行分析
        # 取得計算欄位名稱
        newer_field_name = newer_layer_info['field']
        older_field_name = older_layer_info['field']
        print(newer_field_name)
        # 取得地理空間欄位名稱
        LID_name = newer_layer_info['location_id']
        print(LID_name)

        # 查詢資料
        sdf_newer = item_newer.layers[0].query().df
        sdf_older = item_older.layers[0].query().df

        # 重新命名欄位
        sdf_newer = sdf_newer.rename(columns={
            LID_name: 'LID', newer_field_name: 'VALUE_NEW', 'info_time': 'YEAR_NEW'})
        sdf_older = sdf_older.rename(columns={
            LID_name: 'LID', older_field_name: 'VALUE_OLD', 'info_time': 'YEAR_OLD'})

        # 準備合併用的資料
        sdf_newer_simple = sdf_newer[['LID', 'VALUE_NEW', 'YEAR_NEW', 'SHAPE']]
        sdf_older_simple = sdf_older[['LID', 'VALUE_OLD', 'YEAR_OLD']]

        merged_df = sdf_newer_simple.merge(sdf_older_simple, on='LID')
        merged_df['VALUE_DIFF'] = merged_df['VALUE_NEW'] - merged_df['VALUE_OLD']
        print("資料分析運算完成...")

        # 6. 將結果轉換為 GeoJSON 並回傳
        result_geojson = merged_df.to_json(orient="records")
        
        return Response(result_geojson, mimetype='application/json')

    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
