import requests

url = "https://et-platform-dev3.ikchain.com.cn/api/translation/translate"

headers = {
    "accept": "application/json, text/plain, */*",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOjc2LCJkZXZpY2UiOiJkZWZhdWx0LWRldmljZSIsImVmZiI6MTc1Njg5OTM1NTgzMywicm5TdHIiOiJ4M2x2eHAxaW41SVdsQ2NvU0RObUY1SlFRcnlYNXQxMCJ9.Z6fxS-pFc-GW7UPEmeu82G6JFmQLuWuU0CMINsfosXs",
}

data = {
    "texts": ["Egypt", "China-Taiwan hello world"],
    "fromLanguage": "en",
    "toLanguage": "zh",
}

response = requests.post(url, headers=headers, json=data)

"""

响应 
{
    "code": 0,
    "data": {
        "translatedTexts": [
            "生物力学和生物材料",
            "控制、机器人与动力系统"
        ],
        "fromLanguage": "en",
        "toLanguage": "zh"
    },
    "message": "success",
    "requestId": "106fd6b4-e48f-45cc-a7fe-4b7dbe4d8def"
}
"""
print(response.status_code)
print(response.json())
