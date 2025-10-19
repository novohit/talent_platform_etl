import re

applicant = "CGN Intelligent Manufacturing Technology (Suzhou) Co.,Ltd., Suzhou Nuclear Power Research Institute Co Ltd"

# 通用正则：屏蔽内部逗号，但分隔公司名
pattern = r'(?i)(?<!co\.)(?<!inc)(?<!llc)\s*,\s+(?=[A-Z])'

companies = [x.strip() for x in re.split(pattern, applicant)]
print(companies)
print("------")
