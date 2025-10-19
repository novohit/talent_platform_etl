import pandas as pd
import os

# 设置文件路径
file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'enterprise_papers_with_domains.csv')

# 读取CSV文件
df = pd.read_csv(file_path)

# 对企业单位进行分组统计
enterprise_counts = df['企业单位'].value_counts()

# 筛选数量大于50的企业
filtered_counts = enterprise_counts[enterprise_counts > 50]

# 打印结果
print("\n企业单位统计结果 (论文数量>50):")
print("=" * 50)
print(f"总共有 {len(filtered_counts)} 个企业单位的论文数量超过50篇")
print("\n所有论文数量大于50的企业:")
print(filtered_counts)

# 将结果保存到output目录
output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'enterprise_counts_over_50.csv')
filtered_counts.to_csv(output_path)
print(f"\n结果已保存到: {output_path}")
