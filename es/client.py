from elasticsearch import Elasticsearch
from typing import Dict, Any, List, Optional
from config import config


def get_es_client() -> Elasticsearch:
    """
    获取ES客户端实例
    """
    return Elasticsearch(
        hosts=config.ES_HOSTS,
        basic_auth=(config.ES_USERNAME, config.ES_PASSWORD)
        if config.ES_USERNAME
        else None,
        timeout=config.ES_TIMEOUT,
    )


class ESClient:
    def __init__(self):
        self.client = get_es_client()

    def search(
        self,
        index: str,
        query: Dict[str, Any],
        source: Optional[List[str]] = None,
        size: int = 10,
        from_: int = 0,
    ) -> Dict[str, Any]:
        """
        执行ES查询

        Args:
            index: 索引名称
            query: 查询DSL
            source: 返回字段列表，None表示返回所有字段
            size: 返回文档数量
            from_: 分页起始位置

        Returns:
            查询结果
        """
        body = {"query": query, "size": size, "from": from_}
        if source is not None:
            body["_source"] = source

        response = self.client.search(index=index, body=body)
        return response.body

    def get_by_id(
        self, index: str, doc_id: str, source: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        根据ID获取文档

        Args:
            index: 索引名称
            doc_id: 文档ID
            source: 返回字段列表，None表示返回所有字段

        Returns:
            文档内容
        """
        params = {}
        if source is not None:
            params["_source"] = source

        response = self.client.get(index=index, id=doc_id, **params)
        return response.body

    def delete_by_query(self, index: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据查询条件删除文档

        Args:
            index: 索引名称
            query: 查询DSL

        Returns:
            删除结果
        """
        response = self.client.delete_by_query(index=index, body=query)
        return response.body

    def update_by_query(
        self, index: str, query: Dict[str, Any], script: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据查询条件更新文档

        Args:
            index: 索引名称
            query: 查询DSL
            script: 更新脚本

        Returns:
            更新结果
        """
        body = {"query": query, "script": script}
        response = self.client.update_by_query(index=index, body=body)
        return response.body

    def bulk(
        self, operations: List[Dict[str, Any]], index: str = None
    ) -> Dict[str, Any]:
        """
        执行批量操作

        Args:
            operations: 批量操作的请求体列表，每个操作都是一个字典，
                      包含操作类型（index, create, update, delete）和相应的数据
            index: 可选的默认索引名称

        Returns:
            批量操作结果
        """
        response = self.client.bulk(operations=operations, index=index)
        return response.body


es_client = ESClient()
