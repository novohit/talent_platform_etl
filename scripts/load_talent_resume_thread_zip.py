import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from tqdm import tqdm
from datetime import datetime

base_url = "http://172.22.121.63:32738/api"
pdf_save_path = "../output/resumes_v1"


def fetch_talents(token):
    url = f"{base_url}/talents/filters"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "filters": {"isChinese": ["1"], "major2Domain": ["人工智能"]},
        "keyword": "",
        "page": 0,
        "size": 500,
        "needAggregations": True,
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        return response_data.get("data", {}).get("records", [])
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


def transform_coauthor_data(api_data):
    """
    Transform co-author data from API format to visualization format.

    Args:
        api_data (list): List of co-author data from API

    Returns:
        list: Transformed data containing top 20 co-authors sorted by cooperation count
    """
    # Sort by number of cooperations in descending order
    sorted_data = sorted(
        api_data, key=lambda x: x.get("numCooperation", 0), reverse=True
    )

    # Take only top 20 co-authors
    top_coauthors = sorted_data[:20]

    # Transform the data format
    transformed_data = [
        {
            "text": item.get("partnerName", ""),
            "id": item.get("partnerId", ""),
            "strength": item.get("numCooperation", 0),
        }
        for item in top_coauthors
    ]

    return transformed_data


def transform_to_stream_graph_data(interest_infos):
    """
    Transform interest information into stream graph data format.

    Args:
        interest_infos (list): List of interest information containing keyword and year count data

    Returns:
        list: Transformed data for stream graph visualization
    """
    # Get all unique years from the first interest info's keyword_year_count_info
    years = sorted(
        set(int(item["year"]) for item in interest_infos[0]["keyword_year_count_info"])
    )

    # Create data points for each year
    return [
        {
            "x": year,
            **{
                info["keyword"]: next(
                    (
                        item["count"]
                        for item in info["keyword_year_count_info"]
                        if int(item["year"]) == year
                    ),
                    0,  # default value if year not found
                )
                for info in interest_infos
            },
        }
        for year in years
    ]


def fetch_teacher_papers(teacher_id, token):
    url = f"{base_url}/papers/{teacher_id}/page"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {"page": 1, "size": 1000}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("data", {}).get("list", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching papers for teacher {teacher_id}: {e}")
        return []


def fetch_teacher_collaborations(teacher_id, token):
    url = f"{base_url}/talents/teacher/cooperation?teacherId={teacher_id}&onlyDomestic=false"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching collaborations for teacher {teacher_id}: {e}")
        return []


def fetch_paper_stream_graph(teacher_id, token):
    url = f"{base_url}/talents/paper-stream-graph"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "teacherId": teacher_id,
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching paper stream graph for teacher {teacher_id}: {e}")
        return []


def generate_resume(
    teacher_data,
    papers,
    collaborations=[],
    collaborations_chart=[],
    paper_stream_graph_data=[],
    index=None,
):
    url = "http://172.22.121.63:32301/generate-pdf"
    # url = "http://localhost:3000/generate-pdf"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "teacherData": teacher_data,
        "papers": papers,
        "collaborations": collaborations,
        "relationshipGraph": collaborations_chart,
        "streamGraphData": paper_stream_graph_data,
        "config": {
            "maxPapers": 1000,
            "maxCollaborations": 5,
            "maxMajor2Domain": 10,
            "maxMajor3Domain": 10,
        },
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        # 获取教师姓名，用于文件名
        teacher_name = teacher_data.get("derivedTeacherName", "unknown")
        ranking = teacher_data.get("ranking", "null")
        famous_titles_level = teacher_data.get("famousTitlesLevel", "null")
        job_title_level = teacher_data.get("jobTitleLevel", "null")
        # 构建PDF文件路径，添加序号
        index_str = (
            f"{index:04d}_" if index is not None else ""
        )  # 格式化为3位数，例如：001_
        pdf_path = f"{pdf_save_path}/{index_str}{teacher_name}_papers_{len(papers)}_rank_{ranking}_title_{famous_titles_level}_job_{job_title_level}_resume.pdf"

        # 将PDF内容写入文件
        with open(pdf_path, "wb") as f:
            f.write(response.content)

        return {
            "success": True,
            "file_path": pdf_path,
            "message": f"PDF saved successfully at {pdf_path}",
        }
    except requests.exceptions.RequestException as e:
        print(f"Error generating resume: {e}")
        return None
    except IOError as e:
        print(f"Error saving PDF file: {e}")
        return None


def process_single_talent(talent, token, index=None):
    teacher_id = talent.get("teacherId")
    teacher_name = talent.get("derivedTeacherName")
    if not teacher_id:
        return {
            "success": False,
            "teacher_name": teacher_name,
            "message": "No teacher ID found",
            "index": index,
            "complete_data": None,
        }

    print(f"\nProcessing {teacher_name} (ID: {teacher_id})")
    papers = fetch_teacher_papers(teacher_id, token)
    collaborations = fetch_teacher_collaborations(teacher_id, token)
    collaborations_chart = transform_coauthor_data(collaborations)
    paper_stream_graph = fetch_paper_stream_graph(teacher_id, token)
    paper_stream_graph_data = transform_to_stream_graph_data(paper_stream_graph)

    # 创建完整的教师数据
    complete_data = {
        "index": index,  # 添加序号到数据中
        **talent,  # 包含原始教师数据
        "papers": papers,
        "collaborations": collaborations,
        "collaborations_chart": collaborations_chart,
        "paper_stream_graph": paper_stream_graph,
        "paper_stream_graph_data": paper_stream_graph_data,
    }

    result = generate_resume(
        talent,
        papers,
        collaborations,
        collaborations_chart,
        paper_stream_graph_data,
        index,
    )

    if result is not None:
        complete_data["pdf_path"] = result["file_path"]
        return {
            "success": True,
            "teacher_name": teacher_name,
            "message": result["message"],
            "index": index,
            "complete_data": complete_data,
        }
    else:
        return {
            "success": False,
            "teacher_name": teacher_name,
            "message": "Failed to generate resume",
            "index": index,
            "complete_data": None,
        }


def save_teachers_data_to_json(teachers_data):
    """
    Save all teachers' data to a JSON file.

    Args:
        teachers_data (list): List of dictionaries containing teacher data
    """
    json_save_path = os.path.join(os.path.dirname(pdf_save_path), "teachers_data.json")

    # Sort teachers by ranking
    sorted_teachers = sorted(
        teachers_data, key=lambda x: x.get("ranking", float("inf"))
    )

    try:
        with open(json_save_path, "w", encoding="utf-8") as f:
            json.dump(sorted_teachers, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Teachers data saved to: {json_save_path}")
    except Exception as e:
        print(f"\n❌ Error saving teachers data to JSON: {e}")


if __name__ == "__main__":
    os.makedirs(pdf_save_path, exist_ok=True)

    start_time = datetime.now()
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOjc2LCJkZXZpY2UiOiJkZWZhdWx0LWRldmljZSIsImVmZiI6MTc1MjY1MjU1MjAzOCwicm5TdHIiOiJXT2syeWgzRlFkaGJ1eVd3NkgxamRPbm9DUVFVNUJMMyJ9.OvZKcdEZQk-Eg1rtN35ZYoTxqFh-RMtT9nK-iaq6i4Q"

    print("🔍 Fetching talents list...")
    talents = fetch_talents(token)

    if talents is not None:
        total_talents = len(talents)
        print(f"📋 Found {total_talents} talents to process")

        success_count = 0
        failed_count = 0

        # 创建一个列表来存储所有教师的完整数据
        all_teachers_data = []

        # 使用线程池处理简历生成
        max_workers = min(10, total_talents)
        print(f"⚙️ Using {max_workers} threads for processing")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务，并传入索引
            future_to_talent = {
                executor.submit(process_single_talent, talent, token, idx + 1): talent
                for idx, talent in enumerate(talents)
            }

            # 使用tqdm创建进度条
            with tqdm(
                total=total_talents, desc="Processing resumes", unit="resume"
            ) as pbar:
                # 处理完成的任务
                for future in as_completed(future_to_talent):
                    result = future.result()
                    if result["success"]:
                        success_count += 1
                        status = "✅"
                        # 将完整的教师数据添加到列表中
                        if result["complete_data"]:
                            all_teachers_data.append(result["complete_data"])
                    else:
                        failed_count += 1
                        status = "❌"

                    # 更新进度条，显示序号
                    pbar.update(1)
                    # 显示当前处理的简历状态（包含序号）
                    pbar.set_postfix_str(
                        f"{status} [{result['index']:03d}] {result['teacher_name']}"
                    )

        # 保存所有教师数据到JSON文件
        save_teachers_data_to_json(all_teachers_data)

        # 显示最终统计信息
        end_time = datetime.now()
        duration = end_time - start_time
        print("\n📊 Processing Summary:")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"⏱️ Total time: {duration.total_seconds():.2f} seconds")
        print(
            f"⚡ Average time per resume: {(duration.total_seconds() / total_talents):.2f} seconds"
        )
