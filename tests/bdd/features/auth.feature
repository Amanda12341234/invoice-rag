Feature: 使用者認證
  使用者可以註冊帳號並登入取得 JWT 權杖

  Scenario: 註冊成功
    Given 一個新使用者 "newuser" 密碼 "pass123456"
    When 使用者送出註冊請求
    Then 回應狀態碼為 201
    And 回應包含使用者名稱 "newuser"

  Scenario: 使用者名稱重複
    Given 已存在使用者 "existuser" 密碼 "pass123456"
    When 使用者以 "existuser" 密碼 "pass654321" 送出註冊請求
    Then 回應狀態碼為 409

  Scenario: 登入成功
    Given 已存在使用者 "loginuser" 密碼 "pass123456"
    When 使用者以 "loginuser" 密碼 "pass123456" 送出登入請求
    Then 回應狀態碼為 200
    And 回應包含 access_token

  Scenario: 密碼錯誤
    Given 已存在使用者 "wrongpw" 密碼 "pass123456"
    When 使用者以 "wrongpw" 密碼 "wrongpassword" 送出登入請求
    Then 回應狀態碼為 401

  Scenario: 未帶 token 存取受保護端點
    When 使用者未帶 token 存取受保護端點
    Then 回應狀態碼為 401
