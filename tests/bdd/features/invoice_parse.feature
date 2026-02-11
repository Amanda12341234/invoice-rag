Feature: 發票圖片 AI 解析
  使用者上傳發票照片，AI 解析為結構化資料

  Scenario: 解析成功
    Given 已認證的使用者
    And 一張有效的發票圖片
    When 使用者上傳圖片進行解析
    Then 回應狀態碼為 200
    And 回應包含店名與金額與品項

  Scenario: 無效圖片
    Given 已認證的使用者
    And 一個無效的檔案
    When 使用者上傳檔案進行解析
    Then 回應狀態碼為 422

  Scenario: 分類回退至其他
    Given 已認證的使用者
    And AI 回傳未知分類
    When 使用者上傳圖片進行解析
    Then 解析結果的分類為 "其他"

  Scenario: 驗證錯誤-負數金額
    Given 已認證的使用者
    And AI 回傳負數金額
    When 使用者上傳圖片進行解析
    Then 回應包含驗證錯誤

  Scenario: 解析後圖片未保留
    Given 已認證的使用者
    And 一張有效的發票圖片
    When 使用者上傳圖片進行解析
    Then 伺服器上沒有保留任何圖片檔案
