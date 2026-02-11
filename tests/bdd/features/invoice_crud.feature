Feature: 發票確認儲存與管理
  使用者確認解析結果後儲存，並可瀏覽、編輯、刪除發票

  Scenario: 儲存發票含品項
    Given 已認證的使用者
    When 使用者儲存發票資料
    Then 回應狀態碼為 201
    And 發票包含品項

  Scenario: 發票號碼重複提醒
    Given 已認證的使用者
    And 已存在同號碼發票
    When 使用者儲存同號碼發票
    Then 回應狀態碼為 409

  Scenario: 日期篩選列表查詢
    Given 已認證的使用者
    And 存在多日發票
    When 使用者以日期範圍查詢
    Then 僅回傳範圍內的發票

  Scenario: 取得發票明細
    Given 已認證的使用者
    And 存在一張發票
    When 使用者查詢該發票明細
    Then 回應包含發票與品項

  Scenario: 更新發票
    Given 已認證的使用者
    And 存在一張發票
    When 使用者更新發票店名
    Then 回應包含更新後的店名

  Scenario: 刪除發票同步移除品項與向量
    Given 已認證的使用者
    And 存在一張發票
    When 使用者刪除該發票
    Then 回應狀態碼為 204

  Scenario: 使用者隔離
    Given 使用者 A 有一張發票
    And 使用者 B 已認證
    When 使用者 B 查詢發票列表
    Then 列表為空
