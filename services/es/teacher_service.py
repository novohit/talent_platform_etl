from typing import Dict, Any, List, Optional

from es.client import es_client


class TeacherService:
    """ES教师相关的查询服务"""

    INDEX_NAME = "teachers"

    @classmethod
    def search_by_id(
        cls, teacher_id: str, source: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        根据teacherId搜索教师记录

        Args:
            teacher_id: 教师ID
            source: 返回字段列表，None表示返回所有字段

        Returns:
            查询结果
        """
        query = {"term": {"teacherId.keyword": teacher_id}}

        return es_client.search(
            index=cls.INDEX_NAME,
            query=query,
            source=source,
            size=1,
        )

    @classmethod
    def search_by_name(
        cls,
        name: str,
        source: Optional[List[str]] = None,
        size: int = 10,
        from_: int = 0,
    ) -> Dict[str, Any]:
        """
        根据教师姓名搜索（模糊匹配）

        Args:
            name: 教师姓名
            source: 返回字段列表，None表示返回所有字段
            size: 返回结果数量
            from_: 分页起始位置

        Returns:
            查询结果
        """
        query = {"match": {"name": name}}

        return es_client.search(
            index=cls.INDEX_NAME, query=query, source=source, size=size, from_=from_
        )

    @classmethod
    def search_by_school(
        cls,
        school_id: str,
        source: Optional[List[str]] = None,
        size: int = 10,
        from_: int = 0,
    ) -> Dict[str, Any]:
        """
        根据学校ID搜索教师

        Args:
            school_id: 学校ID
            source: 返回字段列表，None表示返回所有字段
            size: 返回结果数量
            from_: 分页起始位置

        Returns:
            查询结果
        """
        query = {"term": {"schoolId.keyword": school_id}}

        return es_client.search(
            index=cls.INDEX_NAME, query=query, source=source, size=size, from_=from_
        )

    @classmethod
    def search_by_criteria(
        cls,
        school_id: Optional[str] = None,
        subject: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[List[str]] = None,
        size: int = 10,
        from_: int = 0,
    ) -> Dict[str, Any]:
        """
        根据多个条件组合查询教师

        Args:
            school_id: 学校ID（可选）
            subject: 科目（可选）
            status: 教师状态（可选）
            source: 返回字段列表，None表示返回所有字段
            size: 返回结果数量
            from_: 分页起始位置

        Returns:
            查询结果
        """
        must_conditions = []

        if school_id:
            must_conditions.append({"term": {"schoolId.keyword": school_id}})

        if subject:
            must_conditions.append({"term": {"subjects.keyword": subject}})

        if status:
            must_conditions.append({"term": {"status.keyword": status}})

        query = (
            {"bool": {"must": must_conditions}}
            if must_conditions
            else {"match_all": {}}
        )

        return es_client.search(
            index=cls.INDEX_NAME, query=query, source=source, size=size, from_=from_
        )

    @classmethod
    def remove_by_ids(cls, teacher_ids: List[str]) -> Dict[str, Any]:
        """
        根据ID列表删除文档

        Args:
            teacher_ids: 教师ID列表

        Returns:
            删除结果
        """
        query = {"query": {"terms": {"teacherId.keyword": teacher_ids}}}
        response = es_client.delete_by_query(index=cls.INDEX_NAME, query=query)

        return response

    @classmethod
    def update_domains_by_ids(
        cls, teacher_id: str, school_name: str, first_level: List[str]
    ) -> Dict[str, Any]:
        """
        更新教师的学校名称和一级领域

        Args:
            teacher_id: 教师ID
            school_name: 学校名称
            first_level: 一级领域列表

        Returns:
            更新结果
        """
        query = {"term": {"teacherId.keyword": teacher_id}}
        script = {
            "source": """
                ctx._source.schoolName = params.schoolName;
                ctx._source.firstLevel = params.test;
            """,
            "lang": "painless",
            "params": {"schoolName": school_name, "test": first_level},
        }

        return es_client.update_by_query(
            index=cls.INDEX_NAME, query=query, script=script
        )
