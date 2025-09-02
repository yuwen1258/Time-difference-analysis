# 步驟 1: 選擇一個已經預裝好 Miniconda 的官方基礎映像
FROM continuumio/miniconda3

# 步驟 2: 複製您的所有專案檔案到容器中
COPY . /app
WORKDIR /app

# 步驟 3: 建立一個只包含指定版本 Python 的、乾淨的 Conda 環境
RUN conda create -n gis_env python=3.9 -y

# 步驟 4: 提前啟用我們的 Conda 環境，讓後續指令都在此環境中執行
SHELL ["conda", "run", "-n", "gis_env", "/bin/bash", "-c"]

# 步驟 5: 分步安裝套件。我們先從最複雜、最特殊的 esri 頻道安裝 arcgis
# 這樣如果出錯，我們能立刻知道是 arcgis 套件的問題
RUN echo "--- Installing arcgis from esri channel ---" && \
    conda install -c esri arcgis -y

# 步驟 6: 接著從來源更穩定、廣泛的 conda-forge 頻道安裝其他所有套件
RUN echo "--- Installing other packages from conda-forge channel ---" && \
    conda install -c conda-forge \
    geopandas \
    flask \
    flask-cors \
    gunicorn \
    python-dotenv \
    pandas \
    -y

# 步驟 7: 列出最終安裝的所有套件，方便日誌除錯
RUN echo "--- Final package list in gis_env ---" && \
    conda list
EXPOSE 10000

CMD ["conda", "run", "-n", "gis_env", "gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--log-level", "debug"]