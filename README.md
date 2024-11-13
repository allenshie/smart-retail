# smart-retail

## 設定檔

如要調整設定，請移動到 `src/config` 位置並編輯 `config.py` 內容，且已助記各功能。

## 輸出通報影像

如果要輸出通報當前影像，請在 `config.py` 檔內將 `RECORD_MODE` 設定為 `True`。在此之前，請確認專案內是否有 `output` 資料夾。如果沒有，則須創建該資料夾。

## 權重檔案下載

您可以從以下連結下載權重檔案：[下載權重檔案](https://1drv.ms/f/s!AgwNM2sn8WQw1sYU3Agkaau-WwTTEQ?e=l35THC)

## Docker 部署

1. **建立 Docker 映像**：在部署服務前，須先在本機端創建 Docker image，使用指令：
   ```bash
   sh ./scripts/docker_scripts.sh build
   ```

2. **啟動服務**：使用指令：
   ```bash
   sh ./scripts/docker_scripts.sh run
   ```

3. **停止服務**：使用指令：
   ```bash
   sh ./scripts/docker_scripts.sh stop
   ```

4. **刪除容器**：使用指令：
   ```bash
   sh ./scripts/docker_scripts.sh remove
   ```
## 促銷區影像監控測試

如果想針對單一促銷區影像源做監控，可至 `test_promotion.py` 檔內修改 `source` 與 `ROIs_info` 內容，並執行指令：
```bash
python test_promotion.py
```
如果想針對單一體驗區影像源做監控，可至 `test_experience.py` 檔內修改 `source` 內容，並執行指令：
```bash
python test_experience.py
```
在執行前須確保已擁有依賴環境，如果沒有，請使用指令：
```bash
pip install -r requirements.txt
```