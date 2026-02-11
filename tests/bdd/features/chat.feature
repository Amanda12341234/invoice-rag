Feature: RAG 語義對話查詢
  使用者以自然語言提問，系統結合 SQL 精確查詢與語義檢索回答

  Scenario: 聚合查詢
    Given 已認證的使用者有發票資料
    When 使用者問 "這個月花了多少？"
    Then 回應包含答案

  Scenario: 語義搜尋
    Given 已認證的使用者有發票資料
    When 使用者問 "上次買咖啡在哪？"
    Then 回應包含答案

  Scenario: 使用者隔離
    Given 使用者 A 有發票但使用者 B 發問
    When 使用者 B 問 "我花了多少？"
    Then 回應不包含使用者 A 的資料

  Scenario: 回覆使用繁體中文
    Given 已認證的使用者有發票資料
    When 使用者問 "幫我查支出"
    Then 回應使用繁體中文
