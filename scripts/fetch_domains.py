import pymysql
from pymysql import Error
import json
import requests
from typing import List, Dict, Tuple
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 创建线程本地存储
thread_local = threading.local()

class LLMConfig:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

def read_key_domains() -> List[str]:
    """读取重点领域文件"""
    with open('data/重点领域.txt', 'r', encoding='utf-8') as f:
        domains = [line.strip()[3:] for line in f if line.strip()]
    return domains

def create_db_connection():
    """Create database connection."""
    try:
        connection = pymysql.connect(
            host='172.22.121.11',
            port=43200,
            database='personnel-matching-domain-tree',
            user='zwx',
            password='006af022-f15c-442c-8c56-e71a45d4531e'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def fetch_level_3_domains():
    """获取所有三级领域名称"""
    connection = create_db_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `name` FROM domain WHERE `level` = 2"
            cursor.execute(sql)
            results = cursor.fetchall()
            # 将结果转换为简单的列表
            domain_names = [row[0] for row in results]
            return domain_names
    except Error as e:
        print(f"Error executing query: {e}")
        return []
    finally:
        connection.close()

def get_session():
    """获取线程本地的session对象"""
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session

def call_llm_api(llm: LLMConfig, prompt: str) -> str:
    """调用大模型API"""
    url = f"{llm.base_url}/chat/completions"
    headers = llm.get_headers()
    
    data = {
        "model": llm.model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        session = get_session()
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"API调用错误: {e}")
        return None

def process_single_business_domain(args: Tuple[str, List[str], LLMConfig, str]) -> Dict:
    """处理单个业务领域"""
    business_domain, academic_domains, llm, prompt_template = args
    
    prompt = prompt_template.format(
        business_domain=business_domain,
        academic_domains="\n".join(academic_domains)
    )
    
    # 调用大模型API
    response = call_llm_api(llm, prompt)
    if response:
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            print(f"解析结果失败 ({business_domain}): {e}")
            print("原始响应:", response)
    
    return {"business_domain": business_domain, "core_subjects": []}

def analyze_domain_relevance(academic_domains: List[str], business_domains: List[str]) -> List[Dict]:
    """分析每个业务领域的核心支撑学科"""
    api_key = "9d3732d9-0080-4124-9fe9-94c6b3e1f08d"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
    model_name = "doubao-1-5-pro-32k-250115"
    llm = LLMConfig(api_key=api_key, base_url=base_url, model_name=model_name)

    # 构建提示词
    prompt_template = """
    作为南方电网的人才技术专家，请分析以下业务领域需要的核心学科支撑。

    待分析的业务领域：{business_domain}
    
    可选的学科领域列表：
    {academic_domains}

    评判标准（必须同时满足）：
    1. 该学科必须是业务领域的核心基础学科，而不是辅助性学科
    2. 该学科必须来源于可选的学科领域列表，不能胡编乱造

    结果学科必须来源于可选的学科领域列表，不能胡编乱造

    请用JSON格式返回分析结果，格式如下：
    {{
        "business_domain": "{business_domain}",
        "core_subjects": ["核心学科1", "核心学科2"]
    }}
    
    注意：
    1. 只返回相关的领域名称列表
    2. 只需要返回JSON格式数据，不需要其他说明
    """

    results = []
    # 创建任务列表
    tasks = [(domain, academic_domains, llm, prompt_template) for domain in business_domains]
    
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=16) as executor:
        # 提交所有任务并获取future对象
        future_to_domain = {executor.submit(process_single_business_domain, task): task[0] 
                          for task in tasks}
        
        # 使用tqdm显示进度
        with tqdm(total=len(tasks), desc="分析业务领域") as pbar:
            for future in as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"处理业务领域 {domain} 时发生错误: {e}")
                finally:
                    pbar.update(1)
                    # 在每个任务完成后短暂暂停，避免API限流
                    # time.sleep(0.2)
    
    return results

def process_results(results: List[Dict]) -> Dict[str, List[str]]:
    """处理分析结果，按业务领域组织数据"""
    domain_stats = {}
    for result in results:
        business_domain = result.get('business_domain')
        core_subjects = result.get('core_subjects', [])
        if business_domain and core_subjects:
            domain_stats[business_domain] = core_subjects
    return domain_stats



def save_results(domain_stats: Dict[str, List[str]], output_file: str):
    """保存分析结果"""
    # 转换为更易读的格式
    formatted_results = []
    for domain, subjects in domain_stats.items():
        if subjects:  # 只保存有相关学科的领域
            formatted_results.append({
                "重点领域": domain,
                "核心学科数量": len(subjects),
                "核心学科": subjects,
            })
    
    # 按核心学科数量降序排序
    formatted_results.sort(key=lambda x: x["核心学科数量"], reverse=True)
    
    # 保存JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_results, f, ensure_ascii=False, indent=2)

def print_results(domain_stats: Dict[str, List[str]]):
    """打印分析结果"""
    print("\n南方电网重点业务领域核心学科分析结果：")
    print("=" * 80)
    
    # 转换为列表并按核心学科数量排序
    sorted_domains = sorted(
        domain_stats.items(), 
        key=lambda x: len(x[1]), 
        reverse=True
    )
    
    for domain, subjects in sorted_domains:
        if not subjects:
            continue
            
        print(f"\n重点业务领域：{domain}")
        print(f"核心支撑学科数量：{len(subjects)}")
        print("核心支撑学科：")
        # 每行打印2个学科，并标注序号
        for i in range(0, len(subjects), 2):
            subjects_with_index = [f"{j+1}. {subj}" for j, subj in enumerate(subjects[i:i+2], start=i)]
            print("  " + "    ".join(subjects_with_index))
        print(f"\n该领域说明：这些学科是{domain}的核心支撑学科，其专业人才可直接从事该领域的核心技术工作。")
        print("-" * 80)

def main():
    # 获取二级学科领域
    academic_domains = fetch_level_3_domains()
    print(f"找到 {len(academic_domains)} 个二级学科领域")
    
    # 读取业务领域
    business_domains = read_key_domains()
    print(f"找到 {len(business_domains)} 个重点业务领域")
    
    # 分析每个业务领域的核心学科
    results = analyze_domain_relevance(academic_domains, business_domains)
    
    # 处理结果
    domain_stats = process_results(results)
    
    # 保存结果
    save_results(domain_stats, 'output/domain_analysis_results.json')
    
    # 打印结果
    print_results(domain_stats)
    
    print("\n分析完成，详细结果已保存到 output/domain_analysis_results.json")

if __name__ == "__main__":
    main()
