# 步驟 1: 選擇一個已經預裝好 Miniconda 的官方基礎映像
FROM continuumio/miniconda3

# 步驟 2: 將您專案的所有檔案複製到容器的 /app 資料夾中
COPY . /app

# 步驟 3: 設定容器內的工作目錄為 /app
WORKDIR /app

# 步驟 4: 最關鍵的一步！使用 environment.yml 檔案來建立 Conda 環境
# 這會安裝所有指定的套件，包含 arcgis
RUN conda env create -f environment.yml

# 步驟 5: 讓之後的指令預設就在我們建立的 Conda 環境中執行
SHELL ["conda", "run", "-n", "gis_env", "/bin/bash", "-c"]

# 步驟 6: 告訴 Render 我們的應用程式會在哪個 port 運行
EXPOSE 10000

# 步驟 7: 容器啟動時要執行的指令 (使用 gunicorn 啟動 Flask)
# Render 偏好使用 10000 port
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:10000", "app:app"]
#CMD ["python", "-c", "from app import app; print('--- Python Check: Successfully imported app object! ---')"]
