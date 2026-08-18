import requests

# import lxml
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
}

target_url = "https://www.tiobe.com/tiobe-index/"
response = requests.get(target_url, headers=headers, timeout=10)

# 保存HTML文件，用浏览器打开查看
with open("test.csv", "w", encoding="utf-8") as f:
    #     f.write(response.text)
    # print("✅ HTML已保存到 tiobe_debug.html，请打开查看结构")
    # tree = etree.HTML(response.text)
    # table_title = ("姓名,年龄,职业 \n")
    # csv_data = ("frak,23,code enginner \n")
    # f.write(table_title)
    # f.write(csv_data)
    # f.close()
    ...
